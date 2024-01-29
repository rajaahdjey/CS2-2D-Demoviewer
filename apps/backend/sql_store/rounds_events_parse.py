# to parse and store all key events of a round to enable playback and further analysis 
from demoparser2 import DemoParser
import pandas as pd
import numpy as np

# for reference - this match : https://www.hltv.org/stats/matches/mapstatsid/167144/faze-vs-cloud9

# parser = DemoParser("blast-premier-world-final-2023\\84091_mirage.dem")



def pre_requisites(parser):
    #these are info that is needed across other functions - everytime other functions are called, they will call this to get the required details.
    event_names = sorted(parser.list_game_events())
    map_name = parser.parse_header()["map_name"]
    
    if 'begin_new_match' in event_names:
        begin_new_match_df = parser.parse_event('begin_new_match')
        # print(begin_new_match_df)
    else:
        begin_new_match_df = None
    match_start_tick = begin_new_match_df['tick'].iloc[0] if begin_new_match_df is not None else 0
    match_end_tick = parser.parse_event("round_end")["tick"].max()

    return match_start_tick,match_end_tick,map_name

# get flash pops
# get grenade explodes
# get smoke pops 
# get smoke dissipations 
# get molly burns 
# get molly expirations



def restrict_tick_to_match(df,match_start_tick):
    return (df[df['tick']>=match_start_tick])

def grenades_parser(parser,match_id):
    match_start_tick,match_end_tick,map_name = pre_requisites(parser)
    flash_df = parser.parse_event('flashbang_detonate',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    flash_df = restrict_tick_to_match(flash_df,match_start_tick)
    hegrenade_df = parser.parse_event('hegrenade_detonate',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    hegrenade_df = restrict_tick_to_match(hegrenade_df,match_start_tick)
    smoke_b_df = parser.parse_event('smokegrenade_detonate',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    smoke_b_df = restrict_tick_to_match(smoke_b_df,match_start_tick)
    smoke_e_df = parser.parse_event('smokegrenade_expired',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    smoke_e_df = restrict_tick_to_match(smoke_e_df,match_start_tick)
    inferno_s_df = parser.parse_event('inferno_startburn',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    inferno_s_df = restrict_tick_to_match(inferno_s_df,match_start_tick)
    inferno_e_df = parser.parse_event('inferno_expire',other=["total_rounds_played"])[['entityid','tick','x','y','total_rounds_played']]
    inferno_e_df = restrict_tick_to_match(inferno_e_df,match_start_tick)
    

    flash_df['matchid'] = match_id
    hegrenade_df['matchid'] = match_id
    smoke_b_df['matchid'] = match_id
    smoke_e_df['matchid'] = match_id
    inferno_s_df['matchid'] = match_id
    inferno_e_df['matchid'] = match_id

    flash_df['mapname'] = map_name
    hegrenade_df['mapname'] = map_name
    smoke_b_df['mapname'] = map_name
    smoke_e_df['mapname'] = map_name
    inferno_s_df['mapname'] = map_name
    inferno_e_df['mapname'] = map_name

    flash_df['match_lookup'] = flash_df["matchid"].astype('str')+'_'+flash_df["mapname"]
    hegrenade_df['match_lookup'] = hegrenade_df["matchid"].astype('str')+'_'+hegrenade_df["mapname"]
    smoke_b_df['match_lookup'] = smoke_b_df["matchid"].astype('str')+'_'+smoke_b_df["mapname"]
    smoke_e_df['match_lookup'] = smoke_e_df["matchid"].astype('str')+'_'+smoke_e_df["mapname"]
    inferno_s_df['match_lookup'] = inferno_s_df["matchid"].astype('str')+'_'+inferno_s_df["mapname"]
    inferno_e_df['match_lookup'] = inferno_e_df["matchid"].astype('str')+'_'+inferno_e_df["mapname"]

    flash_df['key'] = flash_df["entityid"].astype('str')+'_'+flash_df["matchid"].astype('str')+'_'+flash_df["mapname"]+'_'+flash_df["tick"].astype('str')
    hegrenade_df['key'] = hegrenade_df["entityid"].astype('str')+'_'+hegrenade_df["matchid"].astype('str')+'_'+hegrenade_df["mapname"]+'_'+hegrenade_df["tick"].astype('str')
    smoke_b_df['key'] = smoke_b_df["entityid"].astype('str')+'_'+smoke_b_df["matchid"].astype('str')+'_'+smoke_b_df["mapname"]+'_'+smoke_b_df["tick"].astype('str')
    smoke_e_df['key'] = smoke_e_df["entityid"].astype('str')+'_'+smoke_e_df["matchid"].astype('str')+'_'+smoke_e_df["mapname"]+'_'+smoke_e_df["tick"].astype('str')
    inferno_s_df['key'] = inferno_s_df["entityid"].astype('str')+'_'+inferno_s_df["matchid"]+'_'+inferno_s_df["mapname"]+'_'+inferno_s_df["tick"].astype('str')
    inferno_e_df['key'] = inferno_e_df["entityid"].astype('str')+'_'+inferno_e_df["matchid"].astype('str')+'_'+inferno_e_df["mapname"]+'_'+inferno_e_df["tick"].astype('str')

    return flash_df,hegrenade_df,smoke_b_df,smoke_e_df,inferno_s_df,inferno_e_df

# get details of grenade thrower - for later plotting

def grenade_thrower_parser(parser,match_id):

    match_start_tick,match_end_tick,map_name = pre_requisites(parser)

    all_weapons = parser.parse_event('weapon_fire',player=["X", "Y"],other=["total_rounds_played"])

    flash_df = all_weapons[all_weapons['weapon'=='weapon_flashbang']][['tick','user_X','user_Y','user_name','user_steamid','total_rounds_played']]
    hegrenade_df = all_weapons[all_weapons['weapon'=='weapon_hegrenade']][['tick','user_X','user_Y','user_name','user_steamid','total_rounds_played']]
    smoke_df = all_weapons[all_weapons['weapon'=='weapon_smokegrenade']][['tick','user_X','user_Y','user_name','user_steamid','total_rounds_played']]
    inferno_df = all_weapons[(all_weapons['weapon'=='weapon_incgrenade']) | (all_weapons['weapon'=='weapon_molotov']) ][['tick','user_X','user_Y','user_name','user_steamid','total_rounds_played']]

    flash_df['match_id'] = match_id
    flash_df = restrict_tick_to_match(flash_df,match_start_tick)
    hegrenade_df['match_id'] = match_id
    hegrenade_df = restrict_tick_to_match(hegrenade_df,match_start_tick)
    smoke_df['match_id'] = match_id
    smoke_df = restrict_tick_to_match(smoke_df,match_start_tick)
    inferno_df['match_id'] = match_id
    inferno_df = restrict_tick_to_match(inferno_df,match_start_tick)

    flash_df['mapname'] = map_name
    hegrenade_df['mapname'] = map_name
    smoke_df['mapname'] = map_name
    inferno_df['mapname'] = map_name

    flash_df['match_lookup'] = flash_df["matchid"].astype('str')+'_'+flash_df["mapname"]
    hegrenade_df['match_lookup'] = hegrenade_df["matchid"].astype('str')+'_'+hegrenade_df["mapname"]
    smoke_df['match_lookup'] = smoke_df["matchid"].astype('str')+'_'+smoke_df["mapname"]
    inferno_df['match_lookup'] = inferno_df["matchid"].astype('str')+'_'+inferno_df["mapname"]

    flash_df['key'] = flash_df["matchid"].astype('str')+'_'+flash_df["mapname"]+'_'+flash_df["tick"].astype('str')
    hegrenade_df['key'] = hegrenade_df["matchid"].astype('str')+'_'+hegrenade_df["mapname"]+'_'+hegrenade_df["tick"].astype('str')
    smoke_df['key'] = smoke_df["matchid"].astype('str')+'_'+smoke_df["mapname"]+'_'+smoke_df["tick"].astype('str')
    inferno_df['key'] = inferno_df["matchid"].astype('str')+'_'+inferno_df["mapname"]+'_'+inferno_df["tick"].astype('str')


    return flash_df,hegrenade_df,smoke_df,inferno_df



# get all players and bomb position - once every 64 ticks and their status - alive or dead player , planted , dropped , carried and defused for bomb
# get all player and bomb position for all the other important events as well 

def tick_positions(parser,match_id): 
    match_start_tick,match_end_tick,map_name = pre_requisites(parser)
    important_events = ['bomb_planted','bomb_dropped','bomb_defused','flashbang_detonate','hegrenade_detonate','inferno_startburn','inferno_expire','smokegrenade_detonate','smokegrenade_expired',
                    'player_death','player_hurt','weapon_fire','player_blind']
    
    imp_events_ticks = []

    # Find match start tick

   
    for event in important_events:
        #sometimes event can return empty list aka no matches during parsing - zero bomb defusals in this match https://www.hltv.org/stats/matches/mapstatsid/168204/faze-vs-mouz
        #print(event)
        ticks_parsed = parser.parse_event(event,player=["X", "Y"])
        if(len(ticks_parsed)==0):
            print(f"No parsed elements for event: {event}")
            continue
        ticks = restrict_tick_to_match(ticks_parsed,match_start_tick)
        imp_events_ticks.extend(ticks['tick'].tolist())
    imp_events_ticks.extend(np.arange(match_start_tick,match_end_tick,64).tolist()) #get the remaining ticks to fully display the round (every 64th tick)
    imp_events_ticks.append(match_end_tick) #append last tick value
    imp_events_ticks = sorted(list(set(imp_events_ticks))) #get only unique ticks sorted in ascending order
    #is bomb planted is misspelt as is_bomb_planed . issue here : https://github.com/LaihoE/demoparser/issues/106
    params_needed = ["is_alive", "team_num", "player_name", "player_steamid","X","Y","player_state","which_bomb_zone","last_place_name","is_bomb_planed",'total_rounds_played']
    #don't want equipment value and cash spent -  Equipment value can change when player picks up something from ground and creating headaches with primary key duplicacy
    #equipment value and buy value can be looked at later for round summary ...
    ticks_df = parser.parse_ticks(wanted_props = params_needed,ticks=imp_events_ticks)
    ticks_df['matchid'] = match_id
    ticks_df['mapname'] = map_name
    ticks_df['match_lookup'] = ticks_df["matchid"]+'_'+ticks_df["mapname"]
    ticks_df['key'] = ticks_df["matchid"].astype('str')+'_'+ticks_df["mapname"]+'_'+ticks_df["tick"].astype('str')+'_'+ticks_df['player_steamid'].astype('str')
    #print(ticks_df[['total_rounds_played']])
    ticks_df.drop(columns=['steamid','name'],inplace=True)
    #sometimes multiple events at same tick are overlapping - this is leading to primary key duplication errors
    ticks_df.drop_duplicates(subset=['key'],keep='first',inplace=True)
    #print(ticks_df.key.value_counts())
    #ticks_df.to_csv('ticks_check.csv',index=False)
    return ticks_df


#tick_positions(parser,232324).to_csv('tick_pos_check.csv',index=False)