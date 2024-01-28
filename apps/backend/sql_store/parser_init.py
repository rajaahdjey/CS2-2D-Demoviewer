from demoparser2 import DemoParser
import pandas as pd
import numpy as np

# for reference - this match : https://www.hltv.org/stats/matches/mapstatsid/167144/faze-vs-cloud9

parser = DemoParser("blast-premier-world-final-2023\\84091_mirage.dem")

event_names = sorted(parser.list_game_events())

# print(event_names)

# step 1 get list of unique players and steamids. If steamid's already exist in master db, skip else update player table.


def players_list(parser):
    """
    Takes in the parser instance and processes it to return a set of player names and steam ids - to store in our sql database
    """
    players_list = parser.parse_event("player_team", player=["team_clan_name"])
    # print(players_list[['user_name','user_steamid']].dropna())
    return (
        players_list[["user_steamid", "user_name"]]
        .rename(columns={"user_steamid": "steamid", "user_name": "name"})
        .dropna(how="all")
    )


# step 2 - create a match summary page and adding it to the event name and demo id that we would define in the demo file name and folder name
# get first half stats
# get overall stats
# subtract overall - first half to get 2nd half stats and invert the team_name vals.


def match_summary(parser, event_name, match_id):
    """
    Takes in the parser instance along with filepath and processes it to give match summary along with the event and demo id data we want to maintain
    Event and matchid to be provided when calling the function
    """
    halftime_tick = parser.parse_event("announce_phase_end")["tick"].max()
    gameend_tick = parser.parse_event("round_end")["tick"].max()
    map_name = parser.parse_header()["map_name"]

    # adr cannot be calculated from round summary stats - issue : https://github.com/LaihoE/demoparser/issues/51
    # to do later - ADR from player hurt events (Adding total damage, clamping to player current health before taking hit)

    wanted_fields = [
        "kills_total",
        "deaths_total",
        "mvps",
        "headshot_kills_total",
        "ace_rounds_total",
        "4k_rounds_total",
        "3k_rounds_total",
        "total_rounds_played",
        "team_name",
        "team_clan_name",
    ]
    processed_summary = parser.parse_ticks(wanted_fields, ticks=[halftime_tick])
    processed_summary.rename(
        columns={
            "team_clan_name": "teamname",
            "total_rounds_played": "rounds_firsthalf",
            "team_name": "side_firsthalf",
            "kills_total": "kills_firsthalf",
            "deaths_total": "deaths_firsthalf",
            "headshot_kills_total": "headshot_kills_firsthalf",
            "ace_rounds_total": "ace_rounds_firsthalf",
            "4k_rounds_total": "_4k_rounds_firsthalf",
            "3k_rounds_total": "_3k_rounds_firsthalf",
            "name":"playername"
        },
        inplace=True,
    )
    full_match_data = parser.parse_ticks(wanted_fields, ticks=[gameend_tick])
    full_match_data.rename(
        columns={
            "total_rounds_played": "rounds_total",
            "4k_rounds_total": "_4k_rounds_total",
            "3k_rounds_total": "_3k_rounds_total",
        },
        inplace=True,
    )

    for cols in [
        "rounds",
        "kills",
        "deaths",
        "headshot_kills",
        "ace_rounds",
        "_4k_rounds",
        "_3k_rounds",
    ]:
        processed_summary[f"{cols}_secondhalf"] = (
            full_match_data[f"{cols}_total"] - processed_summary[f"{cols}_firsthalf"]
        )

    processed_summary["side_secondhalf"] = np.where(
        processed_summary["side_firsthalf"] == "CT", "T", "CT"
    )

    processed_summary["tournamentname"] = event_name
    processed_summary["matchid"] = match_id
    processed_summary["mapname"] = map_name
    processed_summary["key"] = processed_summary["matchid"]+'_'+processed_summary["mapname"]+'_'+processed_summary["playername"]
    #print(processed_summary.columns)
    processed_summary.drop(columns=["mvps","tick"],inplace=True)
    # df['ADR'] = df['damage_total']/df['total_rounds_played']
    return processed_summary


# print(match_summary(parser, "some tournament", "420").columns)
# summ = match_summary(parser,"some tournament","420")
# summ.to_csv('test.csv',encoding='UTF-8',index=False)

# print(players_list(parser))


def team_summary(parser, event_name, match_id):
    """
    Takes in the parser instance and gives a breakdown of the team round win details and win reasons on both T and CT Side
    """
    round_end_events = parser.parse_event("round_end", other=["team_clan_name"])

    round_end_events = round_end_events[round_end_events['message']!='#SFUI_Notice_Round_Draw']
    round_end_events = round_end_events[round_end_events['message']!='#SFUI_Notice_Game_Commencing']
    round_summ = (
        round_end_events.groupby(["ct_team_clan_name"])
        .agg(ct_halfroundsplayed=("t_team_clan_name", "count"))
        .reset_index()
    )
    round_summ.rename(columns={"ct_team_clan_name": "teamname"}, inplace=True)
    round_summ["totalroundsplayed"] = round_summ["ct_halfroundsplayed"].sum()
    round_summ["t_halfroundsplayed"] = (
        round_summ["totalroundsplayed"] - round_summ["ct_halfroundsplayed"]
    )
    round_end_events["winning_team"] = round_end_events.apply(
        lambda x: x["ct_team_clan_name"] if x["winner"] == 3 else x["t_team_clan_name"],
        axis=1,
    )
    #a round draw in pro match is when there is a tech pause. This round needs to be removed for all purposes.
    round_end_events = round_end_events[round_end_events['message']!='#SFUI_Notice_Round_Draw']
    round_end_events = round_end_events[round_end_events['message']!='#SFUI_Notice_Game_Commencing']
    #round_end_events.to_csv('round_end_events.csv',index=False)
    round_end_summ = round_end_events.groupby(["message", "winning_team"])[
        ["ct_team_clan_name"]
    ].agg("count")
    rename_dict = {
        "winning_team": "teamname",
        "#SFUI_Notice_Bomb_Defused": "Bomb_Defused",
        "#SFUI_Notice_CTs_Win": "Ts_Eliminated",
        "#SFUI_Notice_Target_Bombed": "Target_Bombed",
        "#SFUI_Notice_Target_Saved": "Target_Saved",
        "#SFUI_Notice_Terrorists_Win": "CTs_Eliminated",
    }
    round_end_cols = pd.DataFrame(
        columns=[
            "teamname",
            "Bomb_Defused",
            "Ts_Eliminated",
            "Target_Bombed",
            "CTs_Eliminated",
            "Target_Saved",
        ]
    )
    round_end_summ = pd.concat(
        [
            round_end_cols,
            round_end_summ.reset_index()
            .pivot(columns="message", index="winning_team", values="ct_team_clan_name")
            .reset_index()
            .fillna(0)
            .rename(columns=rename_dict),
        ]
    )
    round_end_summ.fillna(
        0, inplace=True
    )  # round about way to ensure all outcomes types have some value (atleast zero) to ensure consistency for further aggregations.
    round_end_summ.columns.name = None
    # print(round_end_summ)
    round_summ = pd.merge(round_summ, round_end_summ, how="inner", on="teamname")
    round_summ["t_halfroundswon"] = (
        round_summ["Target_Bombed"] + round_summ["CTs_Eliminated"]
    )
    round_summ["ct_halfroundswon"] = (
        round_summ["Ts_Eliminated"]
        + round_summ["Bomb_Defused"]
        + round_summ["Target_Saved"]
    )
    round_summ["totalroundswon"] = round_summ["t_halfroundswon"]+round_summ["ct_halfroundswon"]
    round_summ["mapname"] = parser.parse_header()["map_name"]
    round_summ["tournamentname"] = event_name
    round_summ["matchid"] = match_id
    round_summ["key"] = round_summ["matchid"]+'_'+round_summ["mapname"]+'_'+round_summ["teamname"]
    # round_summ.drop(columns=['tick'],inplace=True)

    return round_summ


# print("*"*10)


# print(header_data)
# print(team_summary(parser,"event","420"))
# round_end_events = parser.parse_event("round_end", other=["team_clan_name"])
# round_end_events["winning_team"] = round_end_events.apply(
#     lambda x: x["ct_team_clan_name"] if x["winner"] == 3 else x["t_team_clan_name"],
#     axis=1,
# )
# print(round_end_events)
# # poss round end reasons : CTs win - all Ts killed , Target Saved - Ts save , Target Bombed - Ts win by Bomb, Bomb Defused - CTs win by defuse , Terrorists Win - all CTs killed
# print(
#     round_end_events.groupby(["message", "winning_team"])["winning_team"].agg("count")
# )

# cs_win_panel_round[0][1].to_csv('cs_win_panel_round.csv')

# hurt_df[1].to_csv('hurt_events.csv')
# # Currently the event "all" gives you all events. Cursed solution for now
# df = parser.parse_events(["all"])
# df = sorted(df)

# for i,sub_df in enumerate(df):
#     print(f"Dataset {i} Title:",sub_df[0])
#     #print(sub_df[1])
#     #break
#     #sub_df.to_csv('parsed_df.csv',index=False)
# print(df[41][0])
# print(df[41][1])
