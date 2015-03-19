import math
import pandas as pd 
import numpy as np
import time
import retrosheet_html_parser as parser
import itertools
'''
Variable Constants
'''
START_YEAR = 2006;
END_YEAR = 2013;



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Creates the BatterID table and PitcherID table from retrosheet.txt 
and lehman.csv files. Players are chosen based on START_YEAR 
and END_YEAR.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def get_player_IDs():
	player_IDs = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\\GameData\Retrosheet_Player_IDs.txt");
	lehman_master = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\\GameData\Lehman_Data\Master.csv");

	##delete unnecessary columns
	lehman_master = lehman_master.drop(lehman_master.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9]], axis = 1);
	lehman_master = lehman_master.drop(lehman_master.columns[[1, 2, 3, 6, 7, 8]], axis = 1);

	##combine lehman and retrosheet files
	player_ID_table = pd.merge(player_IDs, lehman_master, left_on = 'ID', right_on='retroID');

	#comment block below checked that values between sheets matched. errors were fixed upon discover.
	table_length = player_ID_table.shape[0];
	""" 
		##check that debut dates match
	diff_val_table = pd.DataFrame(data = None);
	for i in range(0, table_length): 
		FIRST = player_ID_table.loc[i, 'DEBUT'];
		firstname = player_ID_table.loc[i, 'debut'];
		if (FIRST != firstname):
			print(player_ID_table.loc[i, 'LAST'] + ", " + player_ID_table.loc[i, 'FIRST'] + ", " +
			player_ID_table.loc[i, 'retroID'] + ", " + player_ID_table.loc[i, 'FIRST'] + 
			player_ID_table.loc[i, 'DEBUT']+ ", " + player_ID_table.loc[i, 'debut']);
	"""

	##reformats date to [year][month][day] format
	for j in range(0, table_length):
		debut_date = player_ID_table.loc[j, 'debut'];
		final_date = player_ID_table.loc[j, 'finalGame'];

		debut_time_obj = time.strptime(debut_date, "%m/%d/%Y");
		final_time_obj = time.strptime(final_date, "%m/%d/%Y");

		debut_formatted = time.strftime("%Y%m%d", debut_time_obj);
		final_formatted = time.strftime("%Y%m%d", final_time_obj);

		player_ID_table.ix[j, 'debut'] = debut_formatted;
		player_ID_table.ix[j, 'finalGame'] = final_formatted;

	##delete duplicate columns and reorder
	player_ID_table = player_ID_table.drop(['playerID', 'DEBUT', 'nameFirst', 'nameLast', 'retroID', 'bbrefID'], axis = 1);
	player_ID_table = player_ID_table.reindex_axis(['ID', 'LAST', 'FIRST', 'debut', 'finalGame', 'bats', 'throws'], axis = 1);



	'''create pitcher table'''

	total_pitcher_stats = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\\GameData\Lehman_Data\Pitching.csv");
	pitcher_ID_table = pd.merge(total_pitcher_stats, lehman_master, left_on = 'playerID', right_on = 'playerID');
	pitcher_ID_table = pitcher_ID_table.drop_duplicates(subset = ['retroID']);

	##merge total playerIDs and pitcherIDs to get activePitcherIDs
	pitcher_ID_table = pd.merge(player_ID_table, pitcher_ID_table, left_on = 'ID', right_on = 'retroID');

	##get rid of extra column labels and reindex
	pitcher_ID_table = pitcher_ID_table.iloc[:, 0:player_ID_table.shape[1]];
	pitcher_ID_table = pitcher_ID_table.reset_index(drop = True);

	## store pitcher table as csv
	pitcher_ID_table.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\pitcher_ID_table.csv");

	

	'''create batter table'''
	batter_ID_table = player_ID_table[player_ID_table.ID.isin(pitcher_ID_table.ID) == False];
	batter_ID_table = batter_ID_table.reset_index(drop = True);

	## store batter table as csv
	batter_ID_table.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\ID_batter_table.csv");





'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Creates the Schedule Table from retrosheet game_log files.
Builds table for years 2006 - 2013. Span adjustable, see constants. 
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def create_schedule_table():
	#define headers and intialize empty schedule_table dataframe
	header_names = ['Date', 'Num of Header', 'Day of Week', 'Visiting Team', 'Visitor League', 'Game Num for Visitor', 
	'Home Team', 'Home League', 'Game Num for Home', 'Time of Day', 'Postponed', 'Makeup'];
	schedule_table = pd.DataFrame(data = np.zeros((0, len(header_names))), columns = header_names);


	#read csv files and append to schedule_table
	for year in range(START_YEAR, END_YEAR + 1):
		file_address = "C:\Users\Brandon\Projects\FantasySportsBaseball\GameData\Game Schedules\_" + str(year) + "Schedule.txt";
		schedule = pd.read_csv(file_address, header = 0, names = header_names);
		schedule_table = schedule_table.append(schedule); 

	##get rid of unnecessary column headers and reorder
	schedule_table = schedule_table.drop(['Num of Header', 'Day of Week', 'Visitor League', 'Game Num for Visitor', 'Home League','Game Num for Home', 'Time of Day'], axis = 1);
	schedule_table = schedule_table.reindex_axis(['Date', 'Home Team', 'Visiting Team', 'Postponed', 'Makeup'], axis = 1);

	## store schedule_table as csv
	schedule_table.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\schedule_table.csv");



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Create Batting Table
-------------------
Iterates through all players in PlayerID table and gets batting 
statistics for all games played between the START_YEAR and 
END_YEAR.

Each iteration appends the batter's statistics to the larger 
Batting_Stats table

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def build_batter_stats_table():

	batter_ID_table = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\ID_batter_table.csv");
	schedule_table = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\schedule_table.csv");

	# creates empty dataframe; formatted to batting stats table

	batter_column_names = ['playerID', 'Date', '#', 'Opponent', 'GS', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'IBB', 'SO', 'HBP', 'SH', 'SF', 'XI', 'ROE', 'GDP', 'SB', 'CS', 'AVG', 'OBP', 'SLG', 'BP', 'Pos'];
	batting_stats_df = pd.DataFrame(data = np.zeros((0, len(batter_column_names))), columns = batter_column_names);
	batting_stats_df.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\stats_batting_table.csv");
	
	#row_start = batter_ID_table.loc[batter_ID_table['playerID'] == 'andeb005'];
	#print row_start
	remaining_players = batter_ID_table.ix[0:, :];
	#print remaining_players;

	
	# append tables to csv file
	with open("C:\Users\Brandon\Projects\FantasySportsBaseball\stats_batting_table.csv", 'a') as f:

	# iterate through batter_ID_tables and get career statistics
		for index, row in remaining_players.iterrows():

			debut_year = int(get_year(str(row.loc['debut'])));
			final_year = int(get_year(str(row.loc['final_game'])));	
			year_beg = debut_year;
			if (debut_year < START_YEAR):
				year_beg = START_YEAR; #only pulling stats from 2006 and up 

			for year in range(year_beg, final_year + 1): ##for entire batter's career, get stats
				player_ID = row.loc['playerID'];
				years_in_mlb = final_year - debut_year + 1;
				tup_val = parser.get_player_stats(player_ID, year, years_in_mlb, True, batter_column_names);
				years_stats = tup_val[1];
				 
				if (tup_val[0]):
					years_stats.to_csv(f, header=False);


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Create Pitching Table
-------------------
Iterates through all players in PlayerID table and gets batting 
statistics for all games played between the START_YEAR and 
END_YEAR.

Each iteration appends the batter's statistics to the larger 
Batting_Stats table
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def build_pitcher_stats_table():
	pitcher_ID_table = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\ID_pitcher_table.csv");
	schedule_table = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\schedule_table.csv");

	pitcher_column_names = ['playerID', 'Date', '#', 'Opponent', 'GS', 'CG', 'SHO', 'GF', 'SV', 'IP', 'H', 'BFP', 'HR', 'R', 'ER', 'BB', 'IB', 'SO', 'SH', 'SF', 'WP', 'HBP', 'BK', '2B', '3B', 'GDP', 'ROE', 'W', 'L', 'ERA'];
	pitcher_stats_df = pd.DataFrame(data = np.zeros((0, len(pitcher_column_names))), columns = pitcher_column_names);
	pitcher_stats_df.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\stats_pitcher_table.csv");


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
format raw data dates
-------------------
Changes dates in raw batting stats to the correct format. 
Creates a new csv file with changes.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''					
def	format_raw_data_dates(filename):
	file_location = "C:\Users\Brandon\Projects\FantasySportsBaseball" + "\\" + filename + ".csv";
	raw_data = pd.read_csv(file_location);

	count = 0;
	table_length = raw_data.shape[0];
	for j in range(0, table_length):
		date = raw_data.loc[j, 'Date'];		
		raw_data.ix[j, 'Date'] = format_date(date);

	raw_data.to_csv(file_location);


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
cull_raw_data
-------------------
Takes raw batting data and formats the table. Deletes unnecessary 
columns and renames it to format for testing.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''	
def cull_raw_data(filename):
	file_location = "C:\Users\Brandon\Projects\FantasySportsBaseball" + "\\" + filename + ".csv";
	batting_table = pd.read_csv(file_location);
	#batting_table = pd.DataFrame(data = np.zeros((0, len(column_names))), columns = column_names);

	# drops unneeded columns
	columns_delete = ['#', 'GS', 'AB', 'SH', 'SF', 'XI', 'ROE', 'GDP', 'AVG', 'OBP', 'SLG', 'BP', 'Pos'];
	batting_table = batting_table.drop(columns_delete, axis=1);
	batting_table = batting_table.drop(batting_table.columns[0:2], axis=1)

	# computes new values for singles and BB columns
	table_length = batting_table.shape[0];
	for row in range(0, table_length):

		# compute singles
		singles = int(batting_table.loc[row, 'H']) - int(batting_table.loc[row, '2B']) - int(batting_table.loc[row, '3B']);
		batting_table.ix[row, 'H'] = singles;
		 
		# compute BB
		bb = int(batting_table.loc[row, 'BB']) + int(batting_table.loc[row, 'IBB']);
		batting_table.ix[row, 'BB'] = bb;


	# delete HBP column
	batting_table = batting_table.drop(['IBB', 'SO'], axis = 1);

	# create new column headers
	column_names = ['batterID', 'Date', 'Opponent', 'R', 'Single', 'Double', 'Triple', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS'];
	batting_table.columns = column_names;
	print batting_table;


	# stores the reformatted table into a new file 
	batting_table.to_csv(file_location);


def create_training_table(filename):
	file_location = "C:\Users\Brandon\Projects\FantasySportsBaseball" + "\\" + filename + ".csv";
	batting_table = pd.read_csv(file_location);




def get_sample_data():
	data = pd.read_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\stats_batting_table_raw.csv");
	sample = data.iloc[0:5000];
	sample.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\sample_data.csv");


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
calc_training_data
-------------------
Takes raw batting data and calculates training features for 'n' past game 
averages. Calculates fantasy sports per game as well. 
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def calc_training_data(filename):
	file_location = "C:\Users\Brandon\Projects\FantasySportsBaseball" + "\\" + filename + ".csv";

	data = pd.read_csv(file_location);

	
	# create column names for training elements
	columns = ['R', 'Single', 'Double','Triple', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS'];
	num_stats = len(columns);
	past_averages = [1, 2, 5, 10, 15, 20, 25];
	col_len = len(columns);

	# create training features
	for num in past_averages:
		suffix = '_' + str(num);
		for j in range(0, col_len):
			columns.append(columns[j] + suffix);


	# get unique IDs
	player_IDs = data.loc[:,'batterID'];
	player_IDs = player_IDs.drop_duplicates();


	training_elements = pd.DataFrame(data = np.zeros((0, len(columns))), columns = columns);
	empty_vals = [None] * num_stats;
	fantasy_points = pd.DataFrame(data = np.zeros((0, 1)), columns = ['fantasy_points']);
	
	fantasy_point_val = [2, 3, 5, 8, 10, 2, 2, 2, 5, -2];


	# iterate through IDs
	num_col = data.shape[1];

	for ID in player_IDs:
		games_for_player = data.loc[data['batterID'] == ID];
		games_for_player = games_for_player.drop(games_for_player.columns[0:1], axis = 1);
		num_games = games_for_player.shape[0];
		r_col_index = games_for_player.columns.get_loc('R');
		col_size = len(games_for_player.columns);

		# iterate through players total games
		for game_num in range(0, num_games):
			train_list = [];
			fantasy_val = [];
			game_vals = list(games_for_player.iloc[game_num, r_col_index:col_size + 1]);
			train_list.append(game_vals);

			fantasy_val.append(np.dot(fantasy_point_val, game_vals));
			

			# iterate through n game averages
			for num in past_averages: #[1, 2, 5, 10, 15, 20, 25];
				if (game_num >= num):

					# calc average over n game
					past_num_games = games_for_player.iloc[(game_num-num):game_num, r_col_index:(col_size + 1)];
					average = list(past_num_games.sum(axis = 0)/num);
					train_list.append(average);
				else:
					train_list.append(empty_vals);
			
			train_list = list(itertools.chain(*train_list));
			temp_df = pd.DataFrame(train_list, index = columns);
			temp_df = temp_df.T;
			pieces = [training_elements, temp_df];
			training_elements = pd.concat(pieces);

			temp_df = pd.DataFrame(fantasy_val, index = ['fantasy_points']);
			temp_df = temp_df.T;
			pieces = [fantasy_points, temp_df];
			fantasy_points = pd.concat(pieces);

	training_elements = pd.concat([training_elements, fantasy_points], axis = 1);
	print fantasy_points;
	training_elements.to_csv("C:\Users\Brandon\Projects\FantasySportsBaseball\sample_training_set.csv")
	










def get_year(date):
	return date[0:4]

def format_date(date):
	## reformats date to [year][month][day] format
	try:
		date_obj = time.strptime(date, "%m-%d-%Y");
		date_formatted = time.strftime("%Y%m%d", date_obj);
		return date_formatted;
	except:
		return date;


def main():
	#get_player_IDs();
	#create_schedule_table();
	#build_batter_stats_table();
	#get_sample_data();
	#format_raw_data_dates("sample_data");
	#cull_raw_data("sample_data");
	#create_training_table("sample_data");
	calc_training_data("sample_data");
	

if __name__ == '__main__':
    main()


