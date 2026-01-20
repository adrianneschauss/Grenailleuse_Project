#Parameters
#Variable n°1 : Temps de production en heure (par exemple 16h)
env_time = 3600/3


#Bottle Arrival
#Variable n°2 : Pourcentage du temps de production ou le chargement est interrompu
#(par exemple 5% de 16h)
down_time = 0.05
#Variable n°5 : Temps de chargement pour une bouteille (par exemple 12 secondes)
mean_interval = 10
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
gr_conv = 4 #the time that we need to discharge (at which point the step conveyour doesnt move)
#for continous stepping the bottle goes from post[0] to post[1] in 56 seconds, but longer due
#to the gr_conv = 12 seconds 
#!!question: shoudl this part be outside of the resource so that the conveyor still moves?

#Continuous Conveyor
#seconds
# Variable n° ? : Nombre de bouteille dans le buffer
length = 457.6
spacing = 30
speed = 15
dt = 1
#capacity = 10
#speed = 9 meters per minute (as i was told)

#Inspector
#Variable n° ? : Temps minimum pour l’inspection de la bouteille ; 
#Variable n° ? : Temps maximum pour l’inspection de la bouteille
inspect_min = 8
inspect_max = 15

#Load and Unload from Inspector 
#Variable n° ? : Vitesse pour transférer une bouteille du déchargement machine jusqu’au chargement de la table d’inspection.
#Variable n° ? : Temps de chargement de la table d’inspection (par exemple 8 secondes), together thats 2+8 
#!!question: should this part be seperated into two? is there a gain there?
t_dis = 10
t_dis2 = 10
#320/ hour 
# 9 meters per minute (max: 16 metre per minute)
#One bottle in vertical: is 300 cm in diameter 
#one bottle needing to be aligned horizontally is equivalent to 926 cm 
#the entire line in either case is equivalent to 5802 cm 

#Horizontal conveyor Additional parameters
length_first = 151.4
#1514
length_second = 390.0
#3900
#3900
vertical_spacing = 30
#300
horizontal_spacing= 92.6
#926
first_speed = 15
second_speed = 15
 #the total length is 4876 but since we need an additional 926 as a sink this is actually only 4876-926

#50 pas minute a 50 hertz 
