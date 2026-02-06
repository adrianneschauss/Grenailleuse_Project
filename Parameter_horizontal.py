#Parameters
#Variable n°1 : Temps de production en heure (par exemple 16h)
env_time = 5000
#57600

#Variable n°2 : Pourcentage du temps de production ou le chargement est interrompu
#(par exemple 5% de 16h)
down_time = 0.10
#Variable n°5 : Temps de chargement pour une bouteille (par exemple 12 secondes)
mean_interval = 12
#Variable n°3 : Temps minimum de l’interruption chargement (par exemple 10 secondes)
min_iter = 10
#Variable n°4 : Temps maximum de l’interruption chargement (par exemple 30 secondes)
max_iter = 30

# WE KNOW: T = m (with prob = 1-p ) and T = M +U (with prob p)
# E[T] = (1-p)*m + p*(m + E[U]) =  m + p E[U]
# E[U] = (min_iter + max_iter)/2
#rate_per_hour = 3600/E[T]
# E[T] = (10 + 0.05*20) = 11
# rate = 3600/ 11 = 327 bottles per hour

# 
#Grenailleuse
#Variable n°6 : Temps de passage à travers la grenailleuse (par exemple 80 secondes)
step_time = 7 #according to jerome 
#Variable n°7 : Nombre de bouteille dans la grenailleuse (par exemple 8 bouteilles)
steps = 8
#Variable n°8 : Temps de déchargement de la bouteille sur le convoyeur (par exemple 12 secondes)
gr_conv = 1 #the time that we need to discharge (at which point the step conveyour doesnt move)
#for continous stepping the bottle goes from post[0] to post[1] in 56 seconds, but longer due
#to the gr_conv = 12 seconds 
#!!question: shoudl this part be outside of the resource so that the conveyor still moves?


#Vertical Conveyor
speed = 10

length = 498

spacing = 30

#Variable conveyor
step_time_2 = 7

first_speed = 10
second_speed = 12

length_first = 151.4
length_second = 395
length_third = 93

vertical_spacing = 35
horizontal_spacing= 85



#Inspector
#Variable n° ? : Temps minimum pour l’inspection de la bouteille ; 
#Variable n° ? : Temps maximum pour l’inspection de la bouteille
inspect_min = 8
inspect_max = 12
min = 30
max = 40
s = 0.05

#Load and Unload from Inspector 
#Variable n° ? : Vitesse pour transférer une bouteille du déchargement machine jusqu’au chargement de la table d’inspection.
#Variable n° ? : Temps de chargement de la table d’inspection (par exemple 8 secondes), together thats 2+8 
#!!question: should this part be seperated into two? is there a gain there?
t_dis = 3
t_dis2 = 3
#Hold time at det2 before inspector (seconds), coneyor that moves to inspector 
det_hold_time = 10
#320/ hour 
# 9 meters per minute(15 cm per second) (max: 16 metre per minute= 26.67 cm per second)
#One bottle in vertical: is 300 cm in diameter 
#one bottle needing to be aligned horizontally is equivalent to 926 cm 
#the entire line in either case is equivalent to 5802 cm 

#Horizontal conveyor Additional parameters

#926

dt = 1
 #the total length is 4876 but since we need an additional 926 as a sink this is actually only 4876-850

#50 pas minute a 50 hertz 

#Mode switch hysteresis (seconds) to prevent rapid toggling
mode_switch_delay = 5
