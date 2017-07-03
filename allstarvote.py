
import json
from math import radians, sin, cos, asin, sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas


def load_nlss_data():
    with open('allstar/NLSS_20170630_.json') as fp:
        data = json.load(fp)
    converted = []
    for county_data in data['per_county_data'].values():
        row = {}
        row['county_name'] = county_data['county_name']
        row['winner'] = county_data.get('winner')
        row['strength'] = county_data.get('strength')
        row['player'] = 'Cozart'
        row['vote'] = county_data.get('vote_details', {}).get('Zack Cozart', 0)
        row['Seager'] = county_data.get('vote_details', {}).get('Corey Seager', 0)
        converted.append(row)
        row = {}
        row['county_name'] = county_data['county_name']
        row['winner'] = county_data.get('winner')
        row['strength'] = county_data.get('strength')
        row['player'] = 'Seager'
        row['vote'] = county_data.get('vote_details', {}).get('Corey Seager', 0)
        converted.append(row)
    return pandas.read_json(json.dumps(converted), orient='records')


def load_county_gazette_data():
    cgaz_df = pandas.read_csv('allstar/2016_Gaz_counties_national.txt',
                              sep='\t', encoding='iso-8859-1')
    cgaz_names = cgaz_df['NAME'].apply(lambda s: s.rsplit(maxsplit=1)[0])
    cgaz_df['county_name'] = cgaz_names + ', ' + cgaz_df['USPS']
    return cgaz_df


def load_division_county_names():
    nlwest = [{'county_name': c} for c in ['San Francisco, CA', 'Denver, CO', 'San Diego, CA', 'Maricopa, AZ', 'Los Angeles, CA']]
    nlcentral = [{'county_name': c} for c in ['Milwaukee, WI', 'Cook, IL', 'St. Louis, MO', 'Allegheny, PA', 'Hamilton, OH']]
    nlw_df = pandas.DataFrame(nlwest)
    nlc_df = pandas.DataFrame(nlcentral)
    return nlw_df, nlc_df


# https://stackoverflow.com/a/15737218
def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km


def distance_to_county(row, lat, long):
    distance = haversine(long, lat, row['INTPTLONG'], row['INTPTLAT'])
    return distance < 50


def main():
    nlss_df = load_nlss_data()
    cgaz_df = load_county_gazette_data()
    df = nlss_df.merge(cgaz_df, left_on='county_name', right_on='county_name')
    df = df[['county_name', 'player', 'vote', 'INTPTLAT', 'INTPTLONG']]
    nlw_df, nlc_df = load_division_county_names()
    nlw_df = nlw_df.merge(df, how='left', on='county_name')
    nlc_df = nlc_df.merge(df, how='left', on='county_name')
    nlw_rel_frames = []
    for _, row in nlw_df.iterrows():
        tmp_df = df[df.apply(distance_to_county, args=(row['INTPTLAT'], row['INTPTLONG']), axis=1)]
        tmp_df['team_county'] = str(row['county_name'])
        nlw_rel_frames.append(tmp_df)
    nlw_rel_df = pandas.concat(nlw_rel_frames)
    nlw_rel_df['division'] = 'west'
    nlc_rel_frames = []
    for _, row in nlc_df.iterrows():
        tmp_df = df[df.apply(distance_to_county, args=(row['INTPTLAT'], row['INTPTLONG']), axis=1)]
        tmp_df['team_county'] = row['county_name']
        nlc_rel_frames.append(tmp_df)
    nlc_rel_df = pandas.concat(nlc_rel_frames)
    nlc_rel_df['division'] = 'central'
    grouped_nlw = nlw_rel_df[['team_county', 'player', 'vote']].groupby(['team_county', 'player'])
    grouped_nlc = nlc_rel_df[['team_county', 'player', 'vote']].groupby(['team_county', 'player'])
    f, a = plt.subplots(1, 2)
    grouped_nlw.mean().unstack('player').sort_values(('vote', 'Seager')).plot.bar(color=['red', 'dodgerblue'], ax=a[0])
    grouped_nlc.mean().unstack('player').sort_values(('vote', 'Cozart')).plot.bar(color=['red', 'dodgerblue'], ax=a[1])
    f.suptitle("NL West & Central All Star Voting % w/in 50km of Division Rival Counties")
    a[0].set_title('NL West')
    a[0].set_ylabel("Vote%")
    a[0].set_xlabel("Division Team County")
    a[0].set_ylim([0, 100])
    a[0].legend(["Zack Cozart", "Corey Seager"])
    a[0].set_yticks(np.arange(0, 101, 10))
    a[1].set_title('NL Central')
    a[1].set_ylabel("Vote%")
    a[1].set_xlabel("Division Team County")
    a[1].set_ylim([0, 100])
    a[1].legend(["Zack Cozart", "Corey Seager"])
    a[1].set_yticks(np.arange(0, 101, 10))
    plt.show()


if __name__ == '__main__':
    main()
