import math
import pandas as pd 
import numpy as np
import time
from bs4 import BeautifulSoup
import requests
import re
import tokenize

def main():
	column_names = 	['playerID', 'Date', '#', 'Opponent', 'GS', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'IBB', 'SO', 'HBP', 'SH', 'SF', 'XI', 'ROE', 'GDP', 'SB', 'CS', 'AVG', 'OBP', 'SLG', 'BP', 'Pos'];

	get_player_stats("denoc001", 2011, 20, True, column_names);

def get_player_stats(player_ID, year, years_in_mlb, batter_bool, column_names):
	
	url = "";
	print str(years_in_mlb);
	for x in range (1, years_in_mlb*2):
		url = get_url(player_ID, year, x, batter_bool);
		batting_stats_table = get_game_table(url);
		if (batting_stats_table != None):
			print ("table found for " + player_ID + " for year: " + str(year));
			batting_stats_df = read_game_table(batting_stats_table, column_names, player_ID);
			tup_val = (True, batting_stats_df);
			return tup_val;
	

	print("no stats found for " + player_ID + " for year: " + str(year));
	tup_val = (False, None);
	return tup_val;

'''
Function: read_game_table
------------------------------------------------------------
Takes the string representing the html table of player statistics and 
stores the values into a dataframe. Certain columns such as Date and 
game location must be modified before storing. 
'''


def read_game_table(game_table, column_names, playerID):
	##iterate through the table, word-by-word, and store into batting table 
	##return formatted batting table dataframe

	#print("at read_game_table");
	game_table = str(game_table);
	table_rows = game_table.split("\n");


	stats_df = pd.DataFrame(data = np.zeros((0, len(column_names))), columns = column_names);

	for row in table_rows:	
		if (not is_table_header(row) and len(row) != 0): ##skips column header rows
			row_values = row.split();
			#check if values are offset by 1 (due to space char in date) (e.g. '4-' '*1-2011') ('0' coded as whitespace)
			#box_pbp_index = 1 or 2 or 3; check where it falls
			offset = 0;
			location_index = 2;
			## check first 3 words
			if ((row_values[1])[0] == 'B'):
				offsest = 0;
			elif ((row_values[2])[0] == 'B'):
				offset = 1

			elif ((row_values[3])[0] == 'B'):
				offset = 2
			location_index = location_index + offset;


			#concatenate location info
			location_info = row_values[(location_index):(location_index + 3)];
			location_info = ' '.join(location_info);

			#concatenate dates
			date_info = row_values[0];
			if ((offset == 1 and len(row_values[1]) != 1) or offset == 2): ##wrong date w/ no doubleheader || wrong date w/ doubleheader
				date_info = row_values[0:2];
				date_info = ''.join(date_info);

			#Create new row 
				
			## add combined location info
			del row_values[location_index:location_index+3];
			row_values.insert(location_index, location_info);
			
			#if offset = 1; could be 2 options: date is messed up || date is ok but doubleheader
			if (offset == 1):
				del row_values[1];
				row_values[0] = date_info;
			elif (offset == 2): ##wrong date w/ doubleheader
				del row_values[0:2];
				row_values[0] = date_info;

			row_values.insert(0, playerID); # add playerID
			if (len(row_values) != len(column_names)): # add None if player position DNE
				row_values.append(None);
			
			##add row to stats_df

			temp_df = pd.DataFrame(row_values, index = column_names);
			temp_df = temp_df.T;
			pieces = [stats_df, temp_df];
			stats_df = pd.concat(pieces);
			

	stats_df = stats_df.reset_index(drop = True);
	return stats_df;



'''
Function: get_url(playerID, year, year_in_mlb, batter_bool)
------------------------------------------------------------
This function returns the url address of a given player. Batter 	
and pitchers have different url formats and will return appropriate 
address. 
'''

def get_url(playerID, year, year_in_mlb, batter_bool):
	#print ("at get_url");

	if (batter_bool): 
		years_as_player = three_digit_format(year_in_mlb);
		url = "http://www.retrosheet.org/boxesetc/" + str(year) + "/I" + playerID + str(years_as_player) + str(year) + '.htm';
		return url;
	else: 
		##return url for pitcher (different format)
		years_as_player = three_digit_format(year_in_mlb);
		url = "http://www.retrosheet.org/boxesetc/" + str(year) + "/K" + playerID + str(years_as_player) + str(year) + ".htm";
		return url;


'''
Function: three_digit_format
------------------------------------------------------------
Returns the correct format for year_in_mlb to be used in the url address.  
'''
def three_digit_format(year_in_mlb):
	if (len(str(year_in_mlb)) == 2):
		return '0'+ str(year_in_mlb);
	else:
		return '00' + str(year_in_mlb); 


'''
Function: get_game_table
------------------------------------------------------------
Iterates through the html text. If a table exists, it will return it. 

'''
def get_game_table(url):
	#print ("at get_game_table");
	##this return a list of lists
	r = requests.get(url);
	data = r.text;
	soup = BeautifulSoup(data);

	#iterate through text between tags <pre>
	for link in soup.find_all('pre'):
		text = link.get_text();
		if (is_table_header(text)):
			table = link.get_text();
			return table;
	
	return None;


'''
Function: is_table_header(text)
------------------------------------------------------------
Takes a string and checks if it represents a table with 
player statistics. It checks if the first 3 words match
the header of the retrosheet tables. 
'''
def is_table_header(text):
	#print ("at_is_header");
	##first 3 words: 'Date' '#' 'Opponent'
	list_words = text.split();
	word_num = 1;
	if(len(list_words) < 3):
		return False;
	if(list_words[0] == 'Date' and list_words[1] == '#' and list_words[2] == 'Opponent'):
		return True;
	else:
		return False; 




if __name__ == '__main__':
	main();






