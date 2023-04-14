from riotwatcher import LolWatcher, ApiError, RateLimiter
import json
from flatten_json import flatten
import pandas
from dotenv import load_dotenv
import os

load_dotenv()

GAME_COUNT = int(os.getenv('GAME_COUNT'))

SERVER = 'EUN1'

API_KEY = os.getenv('API_KEY')
SUMMONER_NAME = os.getenv('STARTER_NAME')

# TODO: goes in main?
# API_KEY = input('Please provide your Riot API key: ')
# SUMMONER_NAME = input('Please provide a summoner name: ')


def transform_game(game):
    result = {}
    result['matchId'] = game['metadata']['matchId']
    result['startTimestamp'] = game['info']['gameStartTimestamp']
    result['endTimestamp'] = game['info']['gameEndTimestamp']
    result['duration'] = game['info']['gameDuration']
    result['gameMode'] = game['info']['gameMode']
    result['players'] = [{
        'puuid': participant['puuid'],
        'summonerName': participant['summonerName'],
        # 'teamId': participant['teamId'],
        'kills': participant['kills'],
        'assists': participant['assists'],
        'deaths': participant['deaths'],
        'lane': participant['individualPosition'],
        'champion': participant['championName'],
        'visionScore': participant['visionScore'],
        'wardsPlaced': participant['wardsPlaced'],
        'wardsKilled': participant['wardsKilled'],
        'visionWardsBought': participant['visionWardsBoughtInGame'],
        # 'totalDamageDealt': participant['totalDamageDealt'],
        # 'totalDamageDealtToChampions': participant['totalDamageDealtToChampions'],
        # 'totalDamageTaken': participant['totalDamageTaken'],
        # 'totalDamageShieldedOnTeammates': participant['totalDamageShieldedOnTeammates'],
        # 'totalHeal': participant['totalHeal'],
        # 'totalHealsOnTeammates': participant['totalHealsOnTeammates'],
        # 'totalMinionsKilled': participant['totalMinionsKilled'],
    } for participant in game['info']['participants']]
    result['winnerTeam'] = 100 if game['info']['participants'][0]['win'] else 200
    return result


def initialize_api():
    api = LolWatcher(API_KEY)

    return api


if __name__ == '__main__':
    print('Started') # needed for the container thing
    api = initialize_api()
    starter_summoner = api.summoner.by_name(SERVER, SUMMONER_NAME)
    starter_puuid = starter_summoner['puuid']

    pending_puuids = set()
    pending_puuids.add(starter_puuid)
    processed_puuids = set()

    games = {}
    current_count = 0
    print("")

    while current_count < GAME_COUNT:
        if len(pending_puuids) == 0:
            print('No more players to check, saving!')
            break
        for puuid in pending_puuids:
            break
        player_games = api.match.matchlist_by_puuid(
            SERVER, starter_puuid, count=100)

        for game_id in player_games:
            if game_id in games:
                continue
            if current_count >= GAME_COUNT:
                break
            loaded_game = api.match.by_id(SERVER, game_id)
            transformed = transform_game(loaded_game)
            games[game_id] = transformed
            print(f'{current_count} games collected', flush=True)
            current_count += 1
            # Comment if only checking for a single user
            pending_puuids.update([player['puuid'] for player in transformed['players'] if player['puuid'] not in processed_puuids])
        pending_puuids.remove(puuid)
        processed_puuids.add(puuid)

    print('')
    print('Collection done, writing results!')

    with open('result.json', 'w') as file:
        json.dump(games, file, indent=2)

    flattened = [flatten(game) for game in games.values()] 
    df = pandas.DataFrame(flattened)

    with pandas.ExcelWriter('result.xlsx') as writer:
        df.to_excel(writer, sheet_name='Games')

    x = input('DONE!!!')
