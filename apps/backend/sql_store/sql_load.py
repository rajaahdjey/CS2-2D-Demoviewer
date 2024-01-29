# Read demos from set folder structure and process info to store in sql 
# Folder struct to be like this : Event name / Demo ID (For now to be renamed manually)

import pandas as pd
import sqlite3
import os
import parser_init
from demoparser2 import DemoParser
import rounds_events_parse
import importlib
import argparse
from pathlib import Path
importlib.reload(rounds_events_parse)

#basic structure to store data 
# [Done] Players Table - steam_id and player names 
# [TBD] Tournament Summary - make from here or scrape from hltv to verify integrity later? - TBD
# [Done] Match Summary - tournament name & match id (from path name) , summary parsed cols 
# [Done] Team Summary - for each match ID and for each team - talk about count of win conditions, later can be aggregated to get T and CT round win % stats
# [Done] Player Ticks - Get player x,y coordinates, dead / alive status for all the important event ticktimes (deaths , fires , nades) and supplement the remaining with every 64th tick
# Parsed Data - match id and then parsed data with the filters used similar to example : https://github.com/LaihoE/demoparser/tree/main/examples/efficiently_parse_multi_events_and_ticks

#basefilepath where all the demos will be stored 
#each set of demos for a competition to be stored in a particular folder.

parser = argparse.ArgumentParser(description = 'Add demo files to the csv')

parser.add_argument('tournament_name',type=str,help="enter tournament name, there must be folder with same name in basefolder")

args = parser.parse_args()

cwd = str(Path(os.getcwd()).parent.parent.parent.parent)

#print(cwd)
basefilepath = cwd + '\\Demo_Files'
print("Base folder set as :" , basefilepath)
tournament_name = args.tournament_name #'blast-premier-world-final-2023' #don't keep any \\ here
print("Processing Tournament : ",tournament_name)

if not os.path.exists('testdb.db'):
    conn = sqlite3.connect('testdb.db')
    cursor = conn.cursor()

    #first half side to indicate T or CT and vice versa for second half team (store both vals for now)
    #two sets of stats to be stored - rounds played first half , kills first half .... mvps first half 

    cursor.execute("""
                    CREATE TABLE players(
                        steamid INTEGER PRIMARY KEY,
                        name TEXT                   
                    )
                   """)
    
    #simply match id cannot be primary key - reason is because there are multiple map demos for each match id.
    cursor.execute("""
                    CREATE TABLE match_summary(
                        key TEXT PRIMARY KEY,
                        matchid INTEGER,
                        mapname TEXT,
                        tournamentname TEXT,
                        playername TEXT,
                        teamname TEXT,
                        steamid INTEGER,
                        side_firsthalf TEXT, 
                        rounds_firsthalf INTEGER,
                        kills_firsthalf INTEGER,
                        deaths_firsthalf INTEGER,
                        headshot_kills_firsthalf INTEGER,
                        ace_rounds_firsthalf INTEGER,
                        _4k_rounds_firsthalf INTEGER,
                        _3k_rounds_firsthalf INTEGER,
                        side_secondhalf TEXT, 
                        rounds_secondhalf INTEGER,
                        kills_secondhalf INTEGER,
                        deaths_secondhalf INTEGER,
                        headshot_kills_secondhalf INTEGER,
                        ace_rounds_secondhalf INTEGER,
                        _4k_rounds_secondhalf INTEGER,
                        _3k_rounds_secondhalf INTEGER
                   )
                    """)
                   
    cursor.execute("""
                    CREATE TABLE team_summary(
                        key TEXT PRIMARY KEY,
                        matchid INTEGER ,
                        mapname TEXT,
                        tournamentname TEXT,
                        teamname TEXT,
                        totalroundsplayed INTEGER,
                        totalroundswon INTEGER,
                        t_halfroundsplayed INTEGER,
                        t_halfroundswon INTEGER,
                        ct_halfroundsplayed INTEGER,
                        ct_halfroundswon INTEGER,
                        Bomb_Defused INTEGER,
                        Ts_Eliminated INTEGER,
                        Target_Saved  INTEGER,
                        Target_Bombed INTEGER,
                        CTs_Eliminated INTEGER

                    )

                    """)

    #do i need primary key here? not really sure. i have match_id and map_name linked --> can reference other tables. 
    #https://stackoverflow.com/questions/8777533/sql-primary-key-is-it-necessary 
    cursor.execute("""
                    CREATE TABLE tick_positions(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        is_bomb_planed BOOLEAN,
                        player_name TEXT,
                        player_steamid INTEGER,
                        team_num TEXT,
                        player_state INTEGER,
                        which_bomb_zone INTEGER,
                        last_place_name INTEGER,
                        is_alive TEXT,
                        X  INTEGER,
                        Y INTEGER,
                        tick INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE flash_grenade(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE he_grenade(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE smoke_bloom(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE smoke_dissipate(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE inferno_burn(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    cursor.execute("""
                    CREATE TABLE inferno_expire(
                        key TEXT PRIMARY KEY,
                        match_lookup TEXT ,
                        matchid INTEGER ,
                        mapname TEXT,
                        tick INTEGER,
                        x INTEGER,
                        y INTEGER,
                        entityid INTEGER,
                        total_rounds_played INTEGER
                    )

                    """)
    
    print("No DB Found. New DB Created. Re-run script to start parsing and storing data in the DB.")


else:
    conn = sqlite3.connect('testdb.db')
    cursor = conn.cursor()
    for demo in os.listdir(basefilepath+"\\"+tournament_name):
        print(f"Processing demo - {demo}")
        
        match_id = demo.split('_')[0]
        parser = DemoParser(basefilepath+"\\"+tournament_name+"\\"+demo)
        #print(parser_init.players_list(parser).reset_index(drop=True))
        players_df = parser_init.players_list(parser).reset_index(drop=True)
        print("Checking new players")
        for i,row in players_df.iterrows():
            #we need to run player names one by one as teams might have added one new player in a match
            #print(players_df.iloc[i:i+1])
            #don't know why this works instead of just using the row from iterrows, dont care.
            try:
                players_df.iloc[i:i+1].to_sql(name='players', con = conn, if_exists='append',index=False)
            except sqlite3.IntegrityError as e:
                #print(f"Skipping duplicated record for primary key") - this message not needed, need to watch out for the other 2 messages more importantly to catch duplicate matches.
                continue
        #in these block we processes a match and map instance as whole, so can keep as is. If map is already processed for match summary, team summary also will get skipped.
        try:
            print("Processing player summary")
            parser_init.match_summary(parser,event_name=tournament_name,match_id=match_id).to_sql(name='match_summary', con = conn, if_exists='append',index=False)
        except sqlite3.IntegrityError as e:
            print(f"Skipping duplicated record for primary key")
            #continue
        try:
            print("Processing Team Summary")
            parser_init.team_summary(parser,event_name=tournament_name,match_id=match_id).to_sql(name='team_summary', con = conn, if_exists='append',index=False)
        except sqlite3.IntegrityError as e:
            print(f"Skipping duplicated record for primary key")
            #continue
        try:
            print("Processing Tick Positions")
            rounds_events_parse.tick_positions(parser,match_id=match_id).to_sql(name='tick_positions', con = conn, if_exists='append',index=False)
        except sqlite3.IntegrityError as e:
            print(f"Skipping duplicated record for primary key {e}")
            #break
            #continue
        try:
            print("Processing Nades")
            flash_df,hegrenade_df,smoke_b_df,smoke_e_df,inferno_s_df,inferno_e_df = rounds_events_parse.grenades_parser(parser,match_id=match_id)
            flash_df.to_sql(name='flash_grenade', con = conn, if_exists='append',index=False)
            hegrenade_df.to_sql(name='he_grenade', con = conn, if_exists='append',index=False)
            smoke_b_df.to_sql(name='smoke_bloom', con = conn, if_exists='append',index=False)
            smoke_e_df.to_sql(name='smoke_dissipate', con = conn, if_exists='append',index=False)
            inferno_s_df.to_sql(name='inferno_burn', con = conn, if_exists='append',index=False)
            inferno_e_df.to_sql(name='inferno_expire', con = conn, if_exists='append',index=False)
        except sqlite3.IntegrityError as e:
            print(f"Skipping duplicated record for primary key {e}")
            continue
        print(f"Demo {demo} processed in tournament {tournament_name}")





