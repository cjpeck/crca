import pandas as pd
import re

columns = [
    'Race Date',
    'Race Discipline',
    'Race Category',
    'Race Gender',
    'Race Class',
    'Race Age Group',
    'Bib Number',
    'Rider First Name',
    'Rider Last Name',
    'Team',
    'Rider License',
    'Rider Place',
]

race_date = '2016-05-29'
race_discipline = 'RR'

fname = 'club_%s.csv' % race_date.replace('-', '')
fname_out = 'club_%s_FINAL.csv' % race_date.replace('-', '')
db = pd.read_excel('../db.xlsx')
df = pd.read_csv(fname, header=[0,1])
del fname
df_out = pd.DataFrame(columns=columns)

def get_rider_row(place, bib_num, race_gender, race_category, race_age_group, race_class):

    # initialize with rider non-specific info
    row_out = {}
    row_out['Race Date'] = race_date
    row_out['Race Discipline'] = race_discipline
    row_out['Race Category'] = race_category
    row_out['Race Gender'] = race_gender
    row_out['Race Class'] = race_class
    row_out['Race Age Group'] = race_age_group
    row_out['Rider Place'] = place

    # cast to integer if it is a number
    try:
        bib_num = int(bib_num)
    except ValueError:
        bib_num = str(bib_num)

    # return if no bib number
    if isinstance(bib_num, int) and bib_num == 0:
        return row_out

    # 1. look up the bib number in the roster
    # 2. if that doesnt work, assume its the USAC license # and try that
    # 3. if that doesnt work, look up USAC license in master USAC list
    if bib_num <= 1500: #is bib #
        db_row = db.ix[db['Race Number'] == bib_num]
        if not len(db_row)==1:
            print 'incorrect number of rows for %d' %bib_num
            import ipdb; ipdb.set_trace()
        row_out['Bib Number'] = bib_num

    elif isinstance(bib_num, int): # is license #
        db_row = db.ix[db['USAC License'] == bib_num]
        if not len(db_row):
            row_out['Rider License'] = bib_num
            return row_out

    elif isinstance(bib_num, str): # is name
        split_name = bib_num.split(' ')

        first_name_exceptions = ['Ann Marie']
        if not len(split_name) == 2:
            if ' '.join(split_name[:2]) in first_name_exceptions:
                first_name = ' '.join(split_name[:2])
                last_name = split_name[-1]
            else:
                raise ValueError('cant parse name %s' %bib_num)
        else:
            first_name, last_name = split_name
        row_out['Rider First Name'] = first_name
        row_out['Rider Last Name'] = last_name
        return row_out

    last_first_name = db_row['Name'].iloc[0].split(', ')

    # fill in rider info
    row_out['Rider First Name'] = last_first_name[1]
    row_out['Rider Last Name'] = last_first_name[0]
    row_out['Team'] = db_row['Team'].iloc[0]
    row_out['Rider License'] = db_row['USAC License'].iloc[0]

    return row_out

def get_rider_info_dict():
    full_info_dict = []
    for catg in df.columns.levels[0]:

        match = re.findall('(M|W)(\d+)\+', catg)
        if not len(match):
            race_category = catg[1:] #'/'.join([x for x in catg[1:]])
            if catg[0] == 'M':
                race_gender = 'Men'
            elif catg[0] == 'W':
                race_gender = 'Women'
            else:
                raise Exception
            race_age_group = '15-99'
            race_class = 'Senior'
        else:
            if match[0][0] == 'M':
                race_gender = 'Men'
            elif match[0][0] == 'W':
                race_gender = 'Women'
            else:
                raise Exception
            race_category = '1234'
            race_age_group = '%s-99' %match[0][1]
            race_class = 'Master'

        df_catg = df[catg]
        placing_nums = df_catg.ix[df_catg['Results'].notnull(), 'Results']
        dnp_nums = df_catg.ix[
            (df_catg['Roster'].notnull()) &
            (~df_catg['Roster'].isin(placing_nums)),
            'Roster'
        ]

        place_num_pairs = zip(placing_nums.index+1, placing_nums.values) #.astype(int))
        place_num_pairs += zip(['DNP'] * len(dnp_nums), dnp_nums) #.values.astype(int))

        full_info_dict.extend([
            get_rider_row(place, bib_num, race_gender, race_category, race_age_group, race_class)
            for place, bib_num in place_num_pairs
        ])
    return full_info_dict

def output_to_csv():
    full_info_dict = get_rider_info_dict()
    df = pd.DataFrame.from_records(full_info_dict)
    df.to_csv(fname_out, header=True, index=False)

if __name__ == '__main__':
    output_to_csv()

