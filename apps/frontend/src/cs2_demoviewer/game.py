#key to do : 

#0. Playback speed controls , round number selection , round progress bar

# 1. Health bar : no health info currently in sql data, implement once available.
# 2. Grenade interaction with smoke : how to add interaction of grenade vs smoke?



import pygame
import pandas as pd
import numpy as np
import sqlite3
import plot_funcs
import time

#2 gui options for pygame that build on top of pygame 
import pygame_gui
import thorpy as tp

conn = sqlite3.connect('testdb.db')
cursor = conn.cursor()
map_name='de_mirage' #hardcoded for now
#query = f"SELECT * FROM team_summary"

#plan is to pull in tick pos df (That already has grenade df) 

#flash - TBD
#smoke pop , smoke dissipate pulled in --> at each tick time, filter df. 
#for each value in smoke pop, add k,v to a smoke dict --> key entity id? Does it remain consistent enough for a short duration?, v position
#for each value in smoke dissipate, when that tick reaches, remove the 

#later --> how to add interaction of grenade vs smoke?
# later --> for now pulling all data in advance when loading app and then selecting b/w match id's 
#later --> transparency for smokes.


query = f"SELECT * FROM tick_positions where mapname LIKE 'de_mirage'"

df = pd.read_sql(query,conn)
#print(df.head())
match_list = df['matchid'].unique()
df [['x_pos','y_pos']] = df.apply(lambda x: plot_funcs.plot_transform(map_name,(x['X'],x['Y'])),axis=1).apply(pd.Series)
df ['is_alive'] = df['is_alive'].replace({1:'alive',0:'dead'}).astype('str')
df ['team_num'] = df['team_num'].astype('str')


pygame.init()

screen_width,screen_height = 1024,1024
screen = pygame.display.set_mode((screen_width,screen_height))

pygame.display.set_caption("Round Playback")

base_folder = 'D:\\DS Workspace\\CS2 Analysis App\\map_images\\'
map_image = f"{base_folder}{map_name}.jpg"
#need to have jpg here, png has a wierd interaction with the shapes drawn where if the shapes fall in the png transparent area, they are not overwritten during next blit and the shape persists.

background_image = pygame.image.load(map_image).convert_alpha()
background_image = pygame.transform.scale(background_image,(screen_width,screen_height))

manager = pygame_gui.UIManager((screen_width, screen_height))

screen.blit(background_image, (0, 0))
# Colors need to be defined upfront eh
ct = (80, 224, 255)
t = (255,0,0)
black = (0, 0, 0)
observer = (0,0,0) #keep observer black for now
white = (255, 255, 255)
smoke_color = (112,132,148) #rand grey rbg for smoke
molly_color = (204,102,0) #rand orange-yellow rgb for molly and incendiary
flash_color = (245,245,245) #whitish but not completely white 
progress_bar_color = (15,220,14) #random green for progress bar

#define zoom and pan init values
zoom = 1.0
pan_x,pan_y = 0,0
drag_mouse = False
last_mouse_pos = None

# Font
font = pygame.font.Font(None, 36)

match_ids = df['matchid'].unique()
selected_match = match_ids[0]

# Pause and resume buttons
paused = True
# primtive way - native to Pygame
# play_button_rect = pygame.Rect(20, 20, 100, 50)
# pause_button_rect = pygame.Rect(140, 20, 100, 50)
# dropdown_rect = pygame.Rect(280, 20, 200, 50)

# Dictionary to store player circles , smokes (bloom and dissipate to trigger adding and deleting vals to the dict)
player_circles = {}
smokes= {}
mollies = {}
flashbangs = {}

def clear_player_movements():
    player_circles.clear()

def clear_nades(): #needed to remove existing nades from playback when changing round.
    smokes.clear()
    mollies.clear()
    flashbangs.clear()


# Function to filter DataFrame based on match_id
def filter_data(match_id):
    return df[df['matchid'] == match_id]

play_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((20, 20), (100, 50)),
                                             text='Play',
                                             manager=manager)

pause_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((140, 20), (100, 50)),
                                             text='Pause',
                                             manager=manager)

rewind_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((280, 20), (100, 50)),
                                             text='Rewind',
                                             manager=manager)

dropdown_button = pygame_gui.elements.UIDropDownMenu(options_list= list(match_ids.astype(str)) , 
                                                     starting_option= str(selected_match),
                                                     relative_rect=pygame.Rect((420, 20), (100, 50)),
                                                    manager=manager)

progress_bar_rect = pygame.Rect(100,150,800,10)



# Function to draw buttons and dropdown
# def draw_ui():
    # #pygame.draw.rect(screen, white, play_button_rect)
    # pygame.draw.rect(screen, white, pause_button_rect)
    # pygame.draw.rect(screen, white, dropdown_rect)
    
    # play_text = font.render('Play', True, black)
    # pause_text = font.render('Pause', True, black)
    # selected_match_text = font.render(str(selected_match), True, black)

    # screen.blit(play_text, (play_button_rect.x + 10, play_button_rect.y + 10))
    # screen.blit(pause_text, (pause_button_rect.x + 10, pause_button_rect.y + 10))
    # screen.blit(selected_match_text, (dropdown_rect.x + 10, dropdown_rect.y + 10))
    

# Function to draw players on the screen
def draw_players(tick_time):
    pygame.display.flip()
    zoomed_background = pygame.transform.scale(background_image, (int(screen_width * zoom), int(screen_height * zoom)))
    screen.blit(zoomed_background, (pan_x*zoom, pan_y*zoom)) #when i am zoomed, my pan x and y gets multiplied by zoom factor 
    filtered_df = filter_data(selected_match)
    match_lookup = filtered_df.match_lookup.iloc[0] #get the lookup value - match id and map name

    #get flash bang explode tick and x,y pos of smoke center
    query_fb = f"SELECT * from flash_grenade WHERE match_lookup LIKE '{match_lookup}' "
    fb_df = pd.read_sql(query_fb,conn)
    fb_df [['x_pos','y_pos']] = fb_df.apply(lambda x: plot_funcs.plot_transform(map_name,(x['x'],x['y'])),axis=1).apply(pd.Series) #why did i name these x,y in small i dunno

    #get smoke bloom start tick and x,y pos of smoke center
    query_sb = f"SELECT * from smoke_bloom WHERE match_lookup LIKE '{match_lookup}' "
    sb_df = pd.read_sql(query_sb,conn)
    sb_df [['x_pos','y_pos']] = sb_df.apply(lambda x: plot_funcs.plot_transform(map_name,(x['x'],x['y'])),axis=1).apply(pd.Series) #why did i name these x,y in small i dunno

    #get molly burn start tick and x,y pos of smoke center
    query_ib = f"SELECT * from inferno_burn WHERE match_lookup LIKE '{match_lookup}' "
    ib_df = pd.read_sql(query_ib,conn)
    ib_df [['x_pos','y_pos']] = ib_df.apply(lambda x: plot_funcs.plot_transform(map_name,(x['x'],x['y'])),axis=1).apply(pd.Series) #why did i name these x,y in small i dunno


    #get smoke and molly end ticks
    query_sd = f"SELECT * from smoke_dissipate WHERE match_lookup LIKE '{match_lookup}' "
    sd_df = pd.read_sql(query_sd,conn)
    # we don't need x and y pos for dissipation , we will just use the entity id
    # sd_df [['x_pos','y_pos']] = sd_df.apply(lambda x: plot_funcs.plot_transform(map_name,(x['X'],x['Y'])),axis=1).apply(pd.Series)

    query_ie= f"SELECT * from inferno_expire WHERE match_lookup LIKE '{match_lookup}' "
    ie_df = pd.read_sql(query_ie,conn)

    for index, row in filtered_df[filtered_df['tick'] == tick_time].iterrows():
        flashbangs.clear() #clear the existing dict of any items - flashbangs needs to be outside so that at the start of every tick, the dict is cleared 
        player_circles[row['player_name']] = (row['x_pos'], row['y_pos'],row['team_num'],row['is_alive'])
        if sb_df[sb_df['tick']==tick_time].shape[0] > 0:
            for index,row in sb_df[sb_df['tick'] == tick_time].iterrows():
                smokes[row['entityid']] = (row['x_pos'], row['y_pos'])
        if sd_df[sd_df['tick']==tick_time].shape[0] > 0:
            for index,row in sd_df[sd_df['tick'] == tick_time].iterrows():
                smokes.pop(row['entityid'],None) #we just pop the grenade out of the dict
        if ib_df[ib_df['tick']==tick_time].shape[0] > 0:
            for index,row in ib_df[ib_df['tick'] == tick_time].iterrows():
                mollies[row['entityid']] = (row['x_pos'], row['y_pos'])
        if ie_df[ie_df['tick']==tick_time].shape[0] > 0:
            for index,row in ie_df[ie_df['tick'] == tick_time].iterrows():
                mollies.pop(row['entityid'],None) #we just pop the grenade out of the dict
        if fb_df[fb_df['tick']==tick_time].shape[0] > 0:
            for index,row in fb_df[fb_df['tick'] == tick_time].iterrows():
                flashbangs[row['entityid']] = (row['x_pos'], row['y_pos']) #get x,y pos of flashbang for current tick


    #draw smokes first then molly and then the players
    #or else smokes are obscuring player positions insided the smoke radius.

    #draw the smokes and refresh display at each time step 
    for smoke_id , pos in smokes.items():
        pygame.draw.circle(screen,smoke_color,(int((pos[0]+pan_x)*zoom),int((pos[1]+pan_y)*zoom)),int(28.8*zoom)) #30 is just arbitrary, to be verified ... #csgo smoke has 144 radius (units unclear) , map scale is 5 --> 144/5 = 28.8
        #ref link for smoke radius in CSGO : https://www.unknowncheats.me/forum/counterstrike-global-offensive/370606-grenade-radius-smoke-molly.html

    for molly_id , pos in mollies.items():
        pygame.draw.circle(screen,molly_color,(int((pos[0]+pan_x)*zoom),int((pos[1]+pan_y)*zoom)),int(24*zoom))  #csgo molly has 120 radius (units unclear) , map scale is 5 --> 120/5 = 24

    
    for flash_id , pos in flashbangs.items():
        print(flashbangs.items)
        pygame.draw.circle(screen,flash_color,(int((pos[0]+pan_x)*zoom),int((pos[1]+pan_y)*zoom)),int(5*zoom))  #smaller radius for flash, just to indicate that there is a flash thrown

    for player , pos in player_circles.items():
        if pos[2] == '3.0':
            color_val = ct
        elif pos[2] == '2.0':
            color_val = t
        else:
            color_val = observer
        if pos[3] == 'alive':
            pygame.draw.circle(screen, color_val, (int((pos[0]+pan_x)*zoom),int((pos[1]+pan_y)*zoom)), int(5*zoom))
        else:
            x_mark = font.render('X',True,color_val)
            screen.blit(x_mark,(int((pos[0]-5+pan_x)*zoom),int((pos[1]-5+pan_y)*zoom)))
    pygame.display.flip()

# Main loop
running = True
tick_times = sorted(df['tick'].unique())
current_tick = 0

clock = pygame.time.Clock()

#moving draw_ui out of the while loop to prevent flickering. draw ui will only get called again when i change the demo - won't work. draw ui needs to run for every blit
time_delta = 1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     mouse_pos = pygame.mouse.get_pos()
        #     #pygame doesn't directly have gui, but it can get collision of mouse click with shapes to act as primitive GUI

        #     if play_button_rect.collidepoint(mouse_pos):
        #         paused = False
        #         # draw_ui()
        #     elif pause_button_rect.collidepoint(mouse_pos):
        #         paused = True
        #         # draw_ui()
        #     elif dropdown_rect.collidepoint(mouse_pos):
        #         selected_match = match_ids[(match_ids == selected_match).argmax() + 1] if selected_match != match_ids[-1] else match_ids[0]
        #         clear_player_movements()
        #         screen.blit(background_image, (0, 0))
        #         current_tick = 0
        #         draw_players(tick_times[current_tick])
        #         # draw_ui()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                zoom += 0.1
            elif event.button == 5:
                zoom -= 0.1 if zoom > 0.1 else 0
            elif event.button ==1:
                drag_mouse = True
                last_mouse_pos = event.pos
                draw_players(tick_times[current_tick])
        elif event.type == pygame.MOUSEBUTTONUP:
            drag_mouse = False
            last_mouse_pos = None
            draw_players(tick_times[current_tick])

        if drag_mouse:
            current_mouse_pos = pygame.mouse.get_pos()
            if last_mouse_pos:
                dx,dy = current_mouse_pos[0]-last_mouse_pos[0],current_mouse_pos[1]-last_mouse_pos[1]
                pan_x += dx
                pan_y += dy
            last_mouse_pos = current_mouse_pos
        
        #for now rewind needs to be clicked and will only work once, so each click to rewind 10 frames to avoid carpal tunnel
        if event.type == pygame_gui.UI_BUTTON_START_PRESS: #why can't you have a button that keeps returning until it remains pressed??
            if (event.ui_element == rewind_button) :
                #time.sleep(5)
                    print("Rewind button pressed")
                    paused = True
                    clear_player_movements()
                    clear_nades()
                    current_tick = max(0,current_tick-10)
                    draw_players(tick_times[current_tick])
                    rewind_button.enable()
            
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == play_button:
                paused = False
            elif event.ui_element == pause_button:
                paused = True
            
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                selected_match = int(event.text)
                current_tick = 0
                clear_player_movements()
                clear_nades()
                screen.blit(background_image, (0, 0))
                draw_players(tick_times[current_tick])
        


        manager.process_events(event)

    print(f"Tick: {current_tick} ")
    if not paused:
        draw_players(tick_times[current_tick])
        current_tick = (current_tick + 1) % len(tick_times)
        progress_percent = current_tick / (len(tick_times)-1)
        #this is progress across the total demo , not round.
        progress_width = int(progress_percent*progress_bar_rect.width)
        #we draw another rectangle on top of the empty progress bar rectangle that kind of helps to anchor the position of the rect - only change being the progress width that we calculate
        progress_bar_filled = pygame.Rect(progress_bar_rect.x,progress_bar_rect.y,progress_width,progress_bar_rect.height)
        pygame.draw.rect(screen,progress_bar_color,progress_bar_filled)

    # Draw UI elements
    # draw_ui()
    manager.update(time_delta)
    manager.draw_ui(screen)
    pygame.display.update()
    clock.tick(5)  # Adjust the frame rate as needed. 1 feels too slow even with taking every 64th tick for filler events.


pygame.quit()