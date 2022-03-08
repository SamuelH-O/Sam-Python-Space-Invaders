# Samuel H-O et un collègue
# Sapce Invaders
# v2.0


#--------------------------------------------------------------Import Modules--------------------------------------------------------------#

try:  # Importation selon les besoins pour 2.x et 3.x.
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.messagebox as tkMessageBox
except BaseException:
    import Tkinter as tk
    import tkFont
    import tkMessageBox

from random import choice
from time import time
from datetime import datetime

#--------------------------------------------------------------Class SpaceInvaders--------------------------------------------------------------#


class SpaceInvaders(object):  # Gère la fenêtre du jeu
    def __init__(self):
        self.root = tk.Tk()
        h = 900
        w = 1150
        print('Window: h = ' + str(h) + ' & w = ' + str(w))
        self.root.geometry('%dx%d+%d+%d' % (w, h, 0, 0))
        self.root.resizable(0, 0)
        self.root.title("Space Invaders")
        self.frame = tk.Frame(self.root)
        self.frame.pack(side="top", fill="both", expand=True)
        self.game = Game(self.root, self.frame, w, h)

    def play(self):  # Début du jeu
        self.game.start()
        self.root.mainloop()

#--------------------------------------------------------------Class Games--------------------------------------------------------------#


class Game(object):  # Gère le canvas, l'animation, les fonctions des touches, le lancement du jeu, le redémarrage du jeu, la fin du jeu, et garde en mémoire la flotte et le défenseur
    def __init__(self, root, frame, width, height):
        self.root = root  # Utile pour fermer la fenêtre
        self.frame = frame
        # La flotte n'est pas ajoutée dans __init__ parce qu'il peut en avoir
        # plusieurs par partie
        self.fleet = None
        self.defender = Defender()
        self.bunkers = []  # Même raison que pour la flotte
        self.defender_dx = 0
        self.tick_counter = 0  # Utile pour compter les ticks mais se remet à 0 à 49, cela permet de compter les aliens et ajouter l'effet de mouvement
        self.height = height
        self.width = width
        self.text_font = tkFont.Font(
            family="Terminal", size=15, weight="normal")
        self.text = None
        self.canvas = tk.Canvas(
            self.frame,
            height=self.height,
            width=self.width,
            bg='black')
        self.canvas.pack()
        self.to_del_expl_list = []  # Liste d'explosions à supprimer
        # Dictionnaire reliant les numéros d'essai et les variables pour
        # calculer le temps
        self.times = {}

    def animation(self):  # Mets à jour le jeu chaque 40 ms (une mise à jour = un tick)
        begin = time()

        # Déplace les aliens
        self.move_aliens_fleet()

        # Déplace le defender selon l'offset definit dans key_press_left,
        # key_press_right, et key_release
        self.defender.move_in(self.canvas, self.defender_dx)

        # Un des aliens de la flotte tir, tous les 20 ticks
        if self.tick_counter % 20 == 0:
            self.fleet.choose_who_fires(
                self.canvas, self.defender, self.bunkers)

        # Une fois que les aliens se sont déplacés choisit une direction
        if self.tick_counter == 49:
            self.fleet.choose_fleet_direction(self.canvas, self.width)
            self.tick_counter = 0
        else:
            self.tick_counter += 1

        # Déplace les balles
        self.move_bullets()

        # Teste si les balles du defender touchent des aliens
        self.fleet.manage_touched_aliens_by(self.canvas, self.defender)

        # Teste si les balles des aliens touchent le defender
        self.defender.touched_by(self.canvas, self.fleet)

        # Teste si les balles touchent des bunkers
        for i in range(len(self.bunkers)):
            self.bunkers[i].touched_by(self.canvas, self.defender, self.fleet)

        # Compte le temps de vie de chaque explosion et les ajoute dans la
        # liste à détruire si elles dépassent leur temps de vie (5 ticks)
        for expl, lifetime in self.fleet.get_expl_and_lifetime().items():
            self.fleet.get_expl_and_lifetime()[expl] += 1
            if lifetime >= 5:
                self.to_del_expl_list.append(expl)

        # Détruit les explosions et vide la liste à détruire
        self.to_del_expl_list = self.fleet.del_expl(
            self.canvas, self.to_del_expl_list)

        end = time()
        if end - begin >= 0.08:
            print("Tick: " + str(end - begin))
        time_offset = 40
        if int((end - begin) * 1000) < 40:
            time_offset = int((end - begin) * 1000)

        # Si le défenseur n'est plus en vie lance le redémarrage du jeu
        if self.defender.get_alive() == False:
            self.restart()
        # Si tous les aliens sont mort déclare le jeu comme gagné et exécute la
        # fonction nécessaire
        elif self.fleet.get_number_of_aliens_alive() == 0:
            self.win()
        # Sinon change de frame/tick
        else:
            self.canvas.after(40 - time_offset, self.animation)

    # Lance l'animation après 500 ms pour que le joueur ait le temps de réagir
    def start_animation(self):
        self.canvas.after(500, self.animation)

    def key_press_left(self, event):  # Mettre la direction vers la gauche
        self.defender_dx = -self.defender.get_move_delta()

    def key_press_right(self, event):  # Mettre la direction vers la droite
        self.defender_dx = self.defender.get_move_delta()

    def key_release(self, event=None):  # Enlever la direction
        self.defender_dx = 0

    def key_press_space(self, event):  # Tirer
        self.defender.fire(self.canvas)

    def move_bullets(self):  # Déplace les balles
        for bullet in self.defender.get_fired_bullets():
            bullet.move_in(self.canvas, self.height)
        if self.fleet is not None:
            self.fleet.move_bullets(self.canvas, self.height)

    def move_aliens_fleet(self):  # Déplace la flotte d'aliens
        # Le compteur de tick est passé en argument pour avoir un mouvement de
        # flotte comme dans le jeu original (voir fleet.move_in)
        self.fleet.move_in(self.canvas, self.tick_counter)

    def start(self, event=None):  # Lance le jeu
        if event is not None:  # Si c'est un redémarrage supprime le texte, dé-lie la touche entrée, remet le défenseur en vie et enlève une vie
            self.canvas.delete(self.text)
            self.text = None
            self.frame.winfo_toplevel().unbind("<Key-Return>")
            self.defender.set_alive(True)
            self.defender.set_lives(self.defender.get_lives() - 1)

        # Si le defender n'a plus de vie et que c'est un redémarage quitte le
        # jeu
        if self.defender.get_lives() < 0 and event is not None:
            self.quit(event)
        else:  # Sinon lie les touches à leurs fonctions réspectives, ajoute la flotte, installe la flotte, les bunker et le defender, puis lance l'animation
            self.frame.winfo_toplevel().bind("<KeyPress-Left>", self.key_press_left)
            self.frame.winfo_toplevel().bind("<KeyPress-q>", self.key_press_left)
            self.frame.winfo_toplevel().bind("<KeyPress-Right>", self.key_press_right)
            self.frame.winfo_toplevel().bind("<KeyPress-d>", self.key_press_right)
            self.frame.winfo_toplevel().bind("<KeyRelease-Left>", self.key_release)
            self.frame.winfo_toplevel().bind("<KeyRelease-q>", self.key_release)
            self.frame.winfo_toplevel().bind("<KeyRelease-Right>", self.key_release)
            self.frame.winfo_toplevel().bind("<KeyRelease-d>", self.key_release)
            self.frame.winfo_toplevel().bind("<KeyPress-space>", self.key_press_space)

            self.times[3 - self.defender.get_lives()] = [time()]

            self.fleet = Fleet()
            self.bunkers = [
                Bunker(
                    100, 560, 20, 20), Bunker(
                    350, 560, 20, 20), Bunker(
                    600, 560, 20, 20), Bunker(
                    850, 560, 20, 20)]
            i = 0
            for bunker in self.bunkers:
                bunker.install_in(self.canvas, i)
                i += 1

            self.defender.install_in(self.canvas)
            self.fleet.install_in(
                self.canvas, (self.width - self.fleet.get_width()) // 2, 5)

            self.start_animation()

    def restart(self):  # Arrête le jeu, affiche le nombre de vies restantes ainsi que la touche requise pour continuer, et lie cette dernière à sa fonction
        self.end()

        if self.defender.get_lives() < 0:
            text = (
                "Vous êtes mort\n" +
                "Il ne vous rest plus de vies\n" +
                "Appuyez sur entrée pour quitter est enregistrer le score.\n" +
                "Le fichier des score se trouvera au même endroit que le programme")
        elif self.defender.get_lives() <= 1:
            text = ("Vous êtes mort\n"
                    + "Il vous reste "
                    + str(self.defender.get_lives())
                    + " vie\nAppuyez sur entrée pour continuer")
        else:
            text = ("Vous êtes mort\n"
                    + "Il vous reste "
                    + str(self.defender.get_lives())
                    + " vies\nAppuyez sur entrée pour continuer")
        self.text = self.canvas.create_text(
            self.width / 2,
            self.height / 2,
            text=text,
            font=self.text_font,
            fill="red",
            justify=tk.CENTER)

        self.frame.winfo_toplevel().bind("<Key-Return>", self.start)

    # Dé-lie les touches, supprime les éléments de la toile et leurs
    # références respectives, remet la direction à 0, supprime et détruit la
    # flotte, supprime et détruit les explosions restantes, et supprime du
    # canvas le défenseur
    def end(self):
        self.frame.winfo_toplevel().unbind("<KeyPress-Left>")
        self.frame.winfo_toplevel().unbind("<KeyPress-q>")
        self.frame.winfo_toplevel().unbind("<KeyPress-Right>")
        self.frame.winfo_toplevel().unbind("<KeyPress-d>")
        self.frame.winfo_toplevel().unbind("<KeyRelease-Left>")
        self.frame.winfo_toplevel().unbind("<KeyRelease-q>")
        self.frame.winfo_toplevel().unbind("<KeyRelease-Right>")
        self.frame.winfo_toplevel().unbind("<KeyRelease-d>")
        self.frame.winfo_toplevel().unbind("<KeyPress-space>")

        # Ajoute les explosions existantes dans la liste à supprimer
        for expl, lifetime in self.fleet.get_expl_and_lifetime().items():
            self.fleet.get_expl_and_lifetime()[expl] += 1
            if lifetime >= 0:
                self.to_del_expl_list.append(expl)

        # Détruit les explosions et vide la liste à détruire
        self.to_del_expl_list = self.fleet.del_expl(
            self.canvas, self.to_del_expl_list)

        # Détruit les balles tirées par le defender
        i = 0
        while i < len(self.defender.get_fired_bullets()):
            bullet = self.defender.get_fired_bullets()[i]
            self.canvas.delete(bullet.get_id())
            i += 1
        for j in range(i):
            self.defender.remove_fired_bullet(
                self.defender.get_fired_bullets()[0])

        # Détruit les bunkers
        i = 0
        while i < len(self.bunkers):
            self.canvas.delete(self.bunkers[i].destroy(self.canvas))
            i += 1

        # Enlever la direction
        self.key_release()

        # Détruit et supprime la flotte
        self.fleet.destroy(self.canvas)
        self.fleet = None

        # Détruit defender mais garde sa la classe dans self.defender
        self.canvas.delete(self.defender.get_id())

        # Ajoute le temps de l'essaie dans self.times
        for start_end_time in self.times.values():
            if len(start_end_time) == 1:
                start_end_time.append(time())

    # Vide la toile avec self.end() affiche le texte de fin et lance
    # self.quit()
    def win(self):
        self.end()

        if self.defender.get_lives() < 0:
            text = (
                "Bravo!\n" +
                "Vous avez vaincu l'attaque de l'empire\n" +
                "Il ne vous restais aucune vie\n" +
                "Pour avoir un score complet consulter le fichier Score.txt qui se trouve dans le même dossier que ce programme\n" +
                "Appuyez sur echap pour quitter est enregistrer le score.\n")
        elif self.defender.get_lives() <= 1:
            text = ("Bravo!\n" +
                    "Vous avez vaincu l'attaque de l'empire\n" +
                    "Il vous restais encore " +
                    str(self.defender.get_lives()) +
                    " vie\n" +
                    "Pour avoir un score complet consulter le fichier Score.txt qui se trouve dans le même dossier que ce programme\n" +
                    "Appuyez sur echap pour quitter est enregistrer le score.\n")
        else:
            text = ("Bravo!\n" +
                    "Vous avez vaincu l'attaque de l'empire\n" +
                    "Il vous restais encore " +
                    str(self.defender.get_lives()) +
                    " vies\n" +
                    "Pour avoir un score complet consulter le fichier Score.txt qui se trouve dans le même dossier que ce programme\n" +
                    "Appuyez sur echap pour quitter est enregistrer le score.\n")

        self.text = self.canvas.create_text(
            self.width / 2,
            self.height / 2,
            text=text,
            font=self.text_font,
            fill="green",
            justify=tk.CENTER)

        self.frame.winfo_toplevel().bind("<Key-Escape>", self.quit)

    # Enregistre le score dans score.txt et ferme le programme
    def quit(self, event):
        now = datetime.now()
        try:  # Si le fichier Score.txt n'existe pas dans le répertoire
            file = open("Score.txt", 'x')

        except BaseException:  # Si le fichier Score.txt existe dans le répertoire
            file = open("Score.txt", 'a')

        file.write("Score du " + now.strftime("%d/%m/%Y %H:%M:%S") + ':\n')
        if self.defender.get_lives() == -1:
            file.write("Nombre d'essaies restants: " +
                       str(self.defender.get_lives() + 1) + " sur 4\n")
        else:
            file.write("Nombre d'essaies restants: " +
                       str(self.defender.get_lives()) + " sur 4\n")
        file.write("Nombre de TIE Fighter (chasseurs TIE) tués: " +
                   str(self.defender.get_n_victims()) +
                   " sur " +
                   str((4 -
                        (self.defender.get_lives() +
                         1)) *
                       50) +
                   "\n")
        file.write("Temps de chaque essaie :\n")
        for essaie_n, start_end_time in self.times.items():
            time = (start_end_time[1] - start_end_time[0])
            if time >= 60:
                file.write("    Essaie n°" +
                           str(essaie_n) +
                           ": " +
                           str(int(time //
                                   60)) +
                           " minute(s) et " +
                           str(int(time %
                                   60)) +
                           " secondes\n")
            else:
                file.write("    Essaie n°" + str(essaie_n) +
                           ": " + str(int(time)) + "secondes\n")
        file.write('\n')

        file.close()

        self.root.destroy()

#--------------------------------------------------------------Class Defender--------------------------------------------------------------#


class Defender(object):  # Gère l'installation du defender, le mouvement du defender, les collisions entre les projectiles et le defender, et le tir du defender
    def __init__(self):
        self.lives = 3
        self.alive = True
        self.width = 60
        self.height = 100
        self.move_delta = 20
        self.id = None
        self.max_fired_bullets = 3
        self.fired_bullets = []
        self.hitbox = []
        self.fire_point = []
        self.n_victims = 0

    def install_in(self, canvas):  # Calcule la position du defender, génère une liste de coordonées pour un polygone, cré le polygone et enregistre son id, cré une hitbox, cré un point de tir

        # Calcule la position du defender en fonction des dimentions du canvas
        # et de la largeur du faucon millenium
        x = 20
        y = int(canvas.cget("height")) - 50

        # Génère une liste de coordonées pour un polygone en forme de faucon
        # millenium avec des divisions de la sa taille indiqué dans self.width
        # et self.height
        xy = [
            x  # x1
            , y  # y1

            , x + self.width // 5  # x2
            , y + self.height // 5  # y2

            , x + self.width // 5 + 0.4 * self.width  # x3
            , y + self.height // 10 + self.height // 5  # y3

            , x + 2 * self.width // 5 + 0.4 * self.width  # x4
            , y + self.height // 10 + self.height // 5  # y4

            , x + 2 * self.width // 5 + 2 * 0.4 * self.width  # x5
            , y + self.height // 5  # y5

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width  # x6
            , y  # y6

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width  # x7
            , y - self.height // 5  # y7

            , x + self.width // 10 + 3 * self.width // 5 + 2 * 0.4 * self.width  # x8
            , y - self.height // 5  # y8

            , x + self.width // 10 + 3 * self.width // 5 + 2 * 0.4 * self.width  # x9
            , y - self.height // 10 - self.height // 5  # y9

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width  # x10
            , y - self.height // 10 - self.height // 5  # y10

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width  # x11
            , y - self.height // 5  # y11

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width - self.width // 2  # x12
            , y - self.height // 5 - 0.4 * self.height  # y12

            , x + 3 * self.width // 5 + 2 * 0.4 * self.width - self.width // 2  # x13
            , y - 0.4 * self.height  # y13

            , x + 3 * self.width // 5 - self.width // 3 + 2 * 0.4 * self.width - self.width // 2  # x14
            , y - 0.4 * self.height  # y14

            , x + 3 * self.width // 5 - self.width // 3 + 2 * 0.4 * self.width - self.width // 2  # x15
            , y - self.height // 5 - 0.4 * self.height  # y15

            , x + 3 * self.width // 5 - self.width // 3 + 2 * 0.4 * self.width - 2 * self.width // 2  # x16
            , y - self.height // 5  # y16
        ]

        # Cré le polygone de couleur grise et enregistre son id
        self.id = canvas.create_polygon(xy, fill="grey", tags="defender")

        # Enregistre les coordonées de l'hitbox en fonction des coordonées de
        # la liste
        self.hitbox = [xy[0], xy[31], xy[14], xy[7]]

        # Enregistre le point de tir en fonction des coordonées de la liste
        self.fire_point = [xy[26] + (xy[24] - xy[26]) / 2, xy[25] - 10]

    def move_in(self, canvas, dx):  # Déplace le defender

        # Si la direction est poitive (vers la droite) et que le defender n'est
        # pas au bord droit avancer vers la droite
        if dx > 0 and canvas.coords(self.id)[14] < canvas.winfo_width() - 20:
            canvas.move(self.id, dx, 0)

            self.hitbox[0] += dx
            self.hitbox[2] += dx

            self.fire_point[0] += dx

        # Si la direction est négative (vers la gauche) et que le defender
        # n'est pas au bord gauche avancer vers la gauche
        if canvas.coords(self.id)[0] > 10 and dx < 0:
            canvas.move(self.id, dx, 0)

            self.hitbox[0] += dx
            self.hitbox[2] += dx

            self.fire_point[0] += dx

    # Si le defender est touché par une balle d'un alien détruir la ballle et
    # tué le defender
    def touched_by(self, canvas, fleet):
        i = 0
        while i < len(fleet.get_aliens_fleet()
                      ):  # Pour chaque alien de la flotte
            alien = fleet.get_aliens_fleet()[i]
            j = 0
            while j < len(alien.get_fired_bullets()
                          ):  # Pour chaque balle tiré par l'alien
                bullet = alien.get_fired_bullets()[j]

                # Met tous ce qui est en colission avec le defender dans la
                # liste bullet_collision
                bullet_collision = canvas.find_overlapping(
                    canvas.coords(
                        bullet.get_id())[0], canvas.coords(
                        bullet.get_id())[1], canvas.coords(
                        bullet.get_id())[2], canvas.coords(
                        bullet.get_id())[3])
                if len(bullet_collision) > 1:  # Si la liste a plus d'un element
                    if self.id in bullet_collision:
                        # Détruir et supprimer la balle et tué le defender
                        canvas.delete(bullet.get_id())
                        alien.remove_fired_bullet(bullet)
                        canvas.delete(self.id)
                        self.alive = False
                j += 1
            i += 1

    def fire(self, canvas):  # Tirer si la limite de tir n'est pas atteinte
        if len(self.fired_bullets) < self.max_fired_bullets:
            x = Bullet(self, "green")
            x.install_in(canvas)
            self.fired_bullets.append(x)

    # Accesseurs move_delta (de combien le defender se déplace à chaque appel
    # de move_in)
    def get_move_delta(self):
        return self.move_delta

    def get_fired_bullets(self):  # Accesseurs fired_bullets (la liste les balles tirés)
        return self.fired_bullets

    # Supprime une balle de fired_bullets
    def remove_fired_bullet(self, fired_bullet):
        self.fired_bullets.remove(fired_bullet)

    def get_id(self):  # Accesseurs id (l'id du defender)
        return self.id

    def get_fire_point(self):  # Accesseurs fire_point (le point où apparaissent les balles)
        return self.fire_point

    def get_lives(self):  # Accesseurs lives (le nombre de vies restantes)
        return self.lives

    def set_lives(self, lives):  # Change le nombre de vies
        self.lives = lives

    def get_alive(self):  # Accesseurs alive (si le defender est en vie)
        return self.alive

    def set_alive(self, alive):  # Défini si le defender est mort ou vivant
        self.alive = alive

    def get_n_victims(self):  # Accesseurs n_victims (le nombre d'aliens tués)
        return self.n_victims

    def add_victim(self):  # Ajoute une victime au compteur de victime
        self.n_victims += 1

#--------------------------------------------------------------Class Bunker--------------------------------------------------------------#


class Bunker(object):  # Gère l'installation d'un bunker, les collisions entre le bunker et les balle, la destruction du bunker
    def __init__(self, x, y, lines, columns):
        self.x = x
        self.y = y
        self.lines = lines
        self.columns = columns
        self.bricks = []
        self.bricks_width_height = 10
        self.width = self.bricks_width_height * self.columns

    def install_in(self, canvas, bunker_n):  # Cré chaque brick dans le bunker
        x_offset = self.x
        y_offset = self.y
        for x in range(0, self.columns - 1):
            for y in range(0, self.lines - 1):
                self.bricks.append(canvas.create_rectangle(
                    # Ajoute des tags pour reconnaitre les bricks sur le canvas
                    x_offset, y_offset, x_offset + self.bricks_width_height, y_offset + self.bricks_width_height, fill="green", outline='', tags=("bunker", str(bunker_n), str(x), str(y))
                )
                )
                y_offset += self.bricks_width_height
            x_offset += self.bricks_width_height
            y_offset = self.y

    # Si une balle touche une brick la supprimer
    def touched_by(self, canvas, defender, fleet):
        i = 0
        while i < len(defender.get_fired_bullets()
                      ):  # Pour chaque balle tiré par le defender
            bullet = defender.get_fired_bullets()[i]

            # Met tous ce qui est en collision avec la balle dans le tuple
            # bullet_collision
            bullet_collision = canvas.find_overlapping(
                canvas.coords(
                    bullet.get_id())[0], canvas.coords(
                    bullet.get_id())[1], canvas.coords(
                    bullet.get_id())[2], canvas.coords(
                    bullet.get_id())[3])
            if len(bullet_collision) > 1:  # Si bullet_collision a plus d'un element
                j = 0
                while j < len(self.bricks):  # Pour chaque brick du bunker
                    brick = self.bricks[j]
                    if brick in bullet_collision:  # Si la balle est dans bullet_collision
                        canvas.delete(brick)  # Détruire la brique
                        try:
                            canvas.delete(bullet.get_id())
                            defender.remove_fired_bullet(bullet)
                        except BaseException:  # Si la balle est déja supprimer
                            pass
                    j += 1
            i += 1
        i = 0
        while i < len(fleet.get_aliens_fleet()):  # Pour chaque alien
            alien = fleet.get_aliens_fleet()[i]
            if alien.get_alive():  # Si l'alien est en vie

                # Met tous ce qui est en collision avec l'alien dans le tuple
                # alien_collision
                alien_collision = canvas.find_overlapping(
                    canvas.coords(
                        alien.get_id())[0], canvas.coords(
                        alien.get_id())[1], canvas.coords(
                        alien.get_id())[24], canvas.coords(
                        alien.get_id())[25])
                # Convertie alien_collision en liste pour pouvoir la modifier
                alien_collision = list(alien_collision)
                # Enlève l'id de l'alien pour n'avoir plus que les id de ce qui
                # est en collision
                alien_collision.remove(alien.get_id())
                if alien_collision != []:  # Si alien_collision n'est pas vide
                    # Si une des brick touche un alien, tuer le defender
                    # (Perdu) et sort de la boucle pour éviter de faire trop de
                    # boucler pour rien
                    for brick in self.bricks:
                        if brick == alien_collision[0]:
                            defender.set_alive(False)
                            break
                j = 0
                while j < len(alien.get_fired_bullets()
                              ):  # Pour chaque balle tiré par l'alien
                    bullet = alien.get_fired_bullets()[j]

                    # Met tous ce qui est en collision avec la balle dans le
                    # tuple bullet_collision
                    bullet_collision = canvas.find_overlapping(
                        canvas.coords(
                            bullet.get_id())[0], canvas.coords(
                            bullet.get_id())[1], canvas.coords(
                            bullet.get_id())[2], canvas.coords(
                            bullet.get_id())[3])
                    if len(
                            bullet_collision) > 1:  # Si bullet_collision a plus d'un element
                        k = 0
                        while k < len(self.bricks):  # Pour chaque balle
                            brick = self.bricks[k]
                            if brick in bullet_collision:  # Si la balle est dans bullet_collision
                                canvas.delete(brick)  # Détruire la brique
                                try:
                                    canvas.delete(bullet.get_id())
                                    alien.remove_fired_bullet(bullet)
                                except BaseException:  # Si la balle est déja supprimer
                                    pass
                            k += 1
                    j += 1
            i += 1

    def destroy(self, canvas):  # Détruit le bunker
        i = 0
        while i < len(self.bricks):
            canvas.delete(self.bricks[i])
            i += 1
        self.bricks.clear()

    def get_lines(self):  # Accesseurs lines (le nombre de ligne du bunker)
        return self.lines

    def get_columns(self):  # Accesseurs columns (le nombre de colonne du bunker)
        return self.columns

    def get_x(self):  # Accesseurs x (coordonnées x du point en haut à gauche du bunker)
        return self.x

    def get_y(self):  # Accesseurs y (coordonnées y du point en haut à gauche du bunker)
        return self.y

    # Accesseurs bricks_width_height (taille d'une brique)
    def get_bricks_width_height(self):
        return self.bricks_width_height

    def get_bricks(self):  # Accesseurs bricks (la liste des briques)
        return self.bricks

    def get_width(self):  # Accesseurs width (la largeure du bunker)
        return self.width

#--------------------------------------------------------------Class Bullet--------------------------------------------------------------#


class Bullet(object):  # Gère l'installation des balles, le mouvement des balles
    def __init__(self, shooter, color):
        self.half_width = 3
        self.height = 40
        self.color = color
        self.speed = 30
        self.id = None
        self.shooter = shooter

    def install_in(self, canvas):  # Détérmine si la balle à installer vient du defender ou des aliens grace à la couleur, installe la balle en conséquence
        if self.color == "green":
            self.id = canvas.create_oval(
                self.shooter.get_fire_point()[0] -
                self.half_width,
                self.shooter.get_fire_point()[1] -
                self.height,
                self.shooter.get_fire_point()[0] +
                self.half_width,
                self.shooter.get_fire_point()[1],
                fill=self.color,
                tags=(
                    "bullet",
                    canvas.gettags(
                        self.shooter.get_id())[0]))
        else:
            self.id = canvas.create_oval(
                self.shooter.get_fire_point()[0] -
                self.half_width,
                self.shooter.get_fire_point()[1] +
                self.height,
                self.shooter.get_fire_point()[0] +
                self.half_width,
                self.shooter.get_fire_point()[1],
                fill=self.color,
                tags=(
                    "bullet",
                    canvas.gettags(
                        self.shooter.get_id())[0],
                    canvas.gettags(
                        self.shooter.get_id())[1],
                    canvas.gettags(
                        self.shooter.get_id())[2]))

    def move_in(self, canvas, height):  # Déplace la balle et la détruit si elle atteint les bords
        if canvas.coords(
                self.id)[1] >= 0 and canvas.coords(
                self.id)[3] <= height:
            if self.color == "green":
                canvas.move(self.id, 0, -self.speed)
            else:
                canvas.move(self.id, 0, self.speed)
        else:
            canvas.delete(self.id)
            self.shooter.remove_fired_bullet(self)

    def get_id(self):  # Accesseurs id (l'id de la balle)
        return self.id

#--------------------------------------------------------------Class Alien--------------------------------------------------------------#


class Alien(
        object):  # Gère l'installation d'un alien, le mouvement de l'alien, et le tir de l'alien
    def __init__(self):
        self.id = None
        self.alive = True
        self.width = 45
        self.height = 45
        self.fire_point = []
        self.fired_bullets = []

    # Génère une liste de coordonées pour un polygone, cré le polygone et
    # enregistre son id, cré un point de tir
    def install_in(self, canvas, x, y, tag):

        # Génère une liste de coordonées pour un polygone en forme de TIE
        # fighter avec des divisions de sa taille indiqué dans self.width et
        # self.height
        xy = [x,
              y,
              x,
              y + self.height,
              x + self.width // 15,
              y + self.height,
              x + self.width // 15,
              y + (6 * (self.height // 15)),
              x + self.width // 15 + (8 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (2 * (self.height // 45)),
              x + self.width // 15 + (8 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (3 * (self.height // 45)),
              x + self.width // 15 + (15 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (10 * (self.height // 45)),
              x + self.width // 15 + (24 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (10 * (self.height // 45)),
              x + self.width // 15 + (31 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (3 * (self.height // 45)),
              x + self.width // 15 + (31 * (self.width // 45)),
              y + (6 * (self.height // 15)) - (2 * (self.height // 45)),
              x + self.width // 15 + (39 * (self.width // 45)),
              y + (6 * (self.height // 15)),
              x + self.width - (self.width // 15),
              y + self.height,
              x + self.width,
              y + self.height,
              x + self.width,
              y,
              x + self.width - (self.width // 15),
              y,
              x + self.width - (self.width // 15),
              y + (7 * (self.height // 15)),
              x + self.width // 15 + (31 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (2 * (self.height // 45)),
              x + self.width // 15 + (31 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (3 * (self.height // 45)),
              x + self.width // 15 + (24 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (10 * (self.height // 45)),
              x + self.width // 15 + (15 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (10 * (self.height // 45)),
              x + self.width // 15 + (8 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (3 * (self.height // 45)),
              x + self.width // 15 + (8 * (self.width // 45)),
              y + (7 * (self.height // 15)) + (2 * (self.height // 45)),
              x + self.width // 15,
              y + (7 * (self.height // 15)),
              x + self.width // 15,
              y]

        # Cré le polygone de couleur grise et enregistre son id
        self.id = canvas.create_polygon(xy, tags=tag, fill="grey")

        # Enregistre le point de tir en fonction des coordonées de la liste
        self.fire_point = [xy[36], xy[37]]

    def move_in(self, canvas, dx, dy):  # Déplace l'alien et son point de tir
        canvas.move(self.id, dx, dy)

        self.fire_point[0] += dx
        self.fire_point[1] += dy

    def fire(self, canvas):  # Tir
        x = Bullet(self, "red")
        x.install_in(canvas)
        self.fired_bullets.append(x)

    def get_fired_bullets(self):  # Accesseurs fired_bullets (la liste les balles tirés)
        return self.fired_bullets

    # Enleve une balle de la liste les balles tirés
    def remove_fired_bullet(self, fired_bullet):
        self.fired_bullets.remove(fired_bullet)

    def get_alive(self):  # Accesseurs alive (si l'alien est en vie ou non)
        return self.alive

    def set_alive(self, alive):  # Rend l'alien commme mort ou viavant
        self.alive = alive

    def get_id(self):  # Accesseurs id (l'id de l'alien)
        return self.id

    def get_fire_point(self):  # Accesseurs fire_point (le point où apparaissent les balles)
        return self.fire_point

    def get_width(self):  # Accesseurs width (la largeur de l'alien)
        return self.width

    def get_height(self):  # Accesseurs height (la hauteur de l'alien)
        return self.height

#--------------------------------------------------------------Class Fleet--------------------------------------------------------------#

# Gère l'installation de la flotte, le choix de la direction de la flotte, le mouvement de la flotte, les collisions entre les aliens et les balle du defender,
# la destruction des exploitons, le choix de l'alien qui va tirer, le
# mouvement des balles, et la destruction de la flotte
class Fleet(object):
    def __init__(self):
        self.aliens_lines = 5
        self.aliens_columns = 10
        self.aliens_inner_gap = 30
        self.alien_x_delta = 30
        self.alien_y_delta = 0
        fleet_size = self.aliens_lines * self.aliens_columns
        self.aliens_fleet = [None] * fleet_size
        self.expl_and_lifetime = {}

    def install_in(self, canvas, x_offeset, y_offset):  # Gère l'instalation de la flotte
        alien_n = 0  # Permet de savoir à quel alien je suis dans la liste
        x = x_offeset  # Le décalage sur l'axe x
        y = y_offset  # Le décalage sur l'axe y
        for line in range(
                0, self.aliens_lines):  # Pour chaque ligne dans self.aliens_lines
            for column in range(
                    0, self.aliens_columns):  # Pour chaque colonne dans self.aliens_columns
                # Ajoute un alien à la flotte
                self.aliens_fleet[alien_n] = Alien()
                self.aliens_fleet[alien_n].install_in(canvas, x, y, ("alien", str(
                    column), str(line)))  # Installe l'alien dans le canvas
                # Ajoute l'écart entre deux aliens + la largeur de l'alien au
                # décalage sur x
                x += self.aliens_inner_gap + \
                    self.aliens_fleet[alien_n].get_width()
                alien_n += 1  # Ajoute 1 au compteur d'alien
            x = x_offeset  # Remet le décalage sur l'axe x à celui de base
            # Ajoute l'écart entre deux aliens + la hauteur de l'alien au
            # décalage sur x
            y += self.aliens_inner_gap + \
                self.aliens_fleet[alien_n - 1].get_height()

    def choose_fleet_direction(self, canvas, width):
        # Récupère les coordonnées de la flotte en tant que groupe
        x1, y1, x2, y2 = canvas.bbox("alien")

        # Si la flotte touche un des cotés aller vers le bas et changer de sens
        if x2 > width - 60:
            if self.get_alien_x_delta() > 0:
                self.set_alien_x_delta(-self.get_alien_x_delta())
            self.set_alien_y_delta(25)
        elif x1 < 60:
            if self.get_alien_x_delta() < 0:
                self.set_alien_x_delta(-self.get_alien_x_delta())
            self.set_alien_y_delta(25)
        elif self.get_alien_y_delta() == 25:
            self.set_alien_y_delta(0)

    def move_in(self, canvas, tick_counter):  # Déplace un alien par tick
        self.aliens_fleet[len(self.aliens_fleet) - 1 - tick_counter].move_in(
            canvas, self.alien_x_delta, self.alien_y_delta)

    # Si un alien vivant est touché par une balle du defender,
    # Cré une explosion et ajoute la au ditionnaire d'explosions et de temps
    # de vie d'explosions (expl_and_lifetime) et met à 0 le temps de vie de
    # cette explosion, détruit l'alien et la balle
    def manage_touched_aliens_by(self, canvas, defender):
        i = 0
        while i < len(defender.get_fired_bullets()
                      ):  # Pour chaque balle tiré par le defender
            bullet = defender.get_fired_bullets()[i]

            # Met tous ce qui est en collision avec la balle dans le tuple
            # bullet_collision
            bullet_collision = canvas.find_overlapping(
                canvas.coords(
                    bullet.id)[0], canvas.coords(
                    bullet.id)[1], canvas.coords(
                    bullet.id)[2], canvas.coords(
                    bullet.id)[3])
            if len(bullet_collision) > 1:  # Si le tuple à plus qu'un id
                j = 0
                while j < len(
                        self.aliens_fleet):  # Pour chaque alien de la flotte
                    alien = self.aliens_fleet[j]
                    if alien.get_alive():  # Qui est vivant
                        if alien.id in bullet_collision:  # Si il est dans bullet_colision

                            # Ajoute une explosion et son temps de vie (0 à sa
                            # création mais augement chaque tick (voir
                            # game.animation))
                            self.expl_and_lifetime[canvas.create_oval(canvas.coords(alien.get_id())[0], canvas.coords(alien.get_id())[
                                                                      1], canvas.coords(alien.get_id())[24], canvas.coords(alien.get_id())[25], fill="#fad726", outline="#fa0000")] = 0
                            alien.set_alive(False)  # Tue l'alien
                            canvas.delete(alien.get_id())  # Détruit-le
                            defender.add_victim()  # Ajoute une victime au compteur de victime
                            canvas.delete(bullet.get_id())  # Détruit la balle
                            defender.remove_fired_bullet(
                                bullet)  # Supprime la balle
                    j += 1
            i += 1

    # def create_expl(self, canvas, h_and_w):
    # 	xy

    # Supprime les explosions passées en paramètre et retourne une liste vide
    def del_expl(self, canvas, to_del_expl_list):
        i = 0
        while i < len(to_del_expl_list):
            canvas.delete(to_del_expl_list[i])
            self.expl_and_lifetime.pop(to_del_expl_list[i])
            i += 1
        return []

    # Si une colonne d'aliens est au dessus de du defender l'alien le plus bas
    # vivant tire, sinon si une colonne d'alien est au dessus d'un bunker
    # l'alien vivant le plus bas tir
    def choose_who_fires(self, canvas, defender, bunkers):
        list_of_valid_columns = []
        highest_line = -1  # La ligne la plus haute viable
        alien_with_the_highest_line = None  # L'alien avec la ligne la plus haute viable
        # (en réalité la ligne la plus haute sera la plus basse parce que les lignes commencent à 0 en haut et augmentent en descendant)
        # Representation de la flotte en jeu avec leur numéro de colonne et de ligne
        # 00 01 02 03 04
        # 10 11 12 13 14
        # 20 21 22 23 24
        # 30 31 32 33 34

        # Sélection colonne
        for alien in self.aliens_fleet:  # Pour chaque alien
            if alien.get_alive():  # Si l'alien est en vie
                # Si la colonne n'est pas dans la liste des colones valides
                if int(canvas.gettags(alien.get_id())[
                       1]) not in list_of_valid_columns:
                    if alien.get_fire_point()[0] > defender.get_fire_point()[0] - 15 and alien.get_fire_point(
                    )[0] < defender.get_fire_point()[0] + 15:  # Si la colonne d'alien est en face du defender
                        # Ajoute cette colonne comme colone valide
                        list_of_valid_columns.append(
                            int(canvas.gettags(alien.get_id())[1]))
        if list_of_valid_columns == []:  # Si il n'y a pas de colonne valide
            for alien in self.aliens_fleet:  # Pour chaque alien
                if alien.get_alive():  # Si l'alien est en vie
                    # Si la colonne n'est pas dans la liste des colones valides
                    if int(canvas.gettags(alien.get_id())[
                           1]) not in list_of_valid_columns:
                        for bunker in bunkers:  # Pour chaque bunker
                            if alien.get_fire_point()[0] > bunker.get_x() and alien.get_fire_point()[
                                    0] < bunker.get_x() + bunker.get_width():  # Si la colonne d'alien est en face du bunker
                                # Ajoute cette colonne comme colone valide
                                list_of_valid_columns.append(
                                    int(canvas.gettags(alien.get_id())[1]))

        # Choisi au hasard une colonne valide
        valid_column = choice(list_of_valid_columns)

        # Sélection ligne
        for alien in self.aliens_fleet:  # Pour chaque alien
            if alien.get_alive():  # Si l'alien est en vie
                if int(canvas.gettags(alien.get_id())[
                       1]) == valid_column:  # Si l'alien fait partie de la colonne choisie
                    if int(canvas.gettags(alien.get_id())[
                           2]) > highest_line:  # Si l'alien est l'alien vivant le plus bas trouvé
                        # Remplacer l'alien le plus bas par celui troué
                        alien_with_the_highest_line = alien
                        highest_line = int(canvas.gettags(alien_with_the_highest_line.get_id())[
                                           2])  # Remplace la ligne la plus basse par celle trouvé

        if alien_with_the_highest_line is not None:  # Si un alien viable à été trouvé
            alien_with_the_highest_line.fire(canvas)  # Tire sur l'alien

    def move_bullets(self, canvas, height):  # Déplace les balles tirées par chaque alien
        for alien in self.aliens_fleet:
            for bullet in alien.get_fired_bullets():
                bullet.move_in(canvas, height)

    def destroy(self, canvas):  # Détruit chaque alien dans la flotte ainsi que leur balles
        i = 0
        while i < len(self.aliens_fleet):
            bullets = self.aliens_fleet[i].get_fired_bullets()
            j = 0
            while j < len(bullets):
                canvas.delete(
                    self.aliens_fleet[i].get_fired_bullets()[j].get_id())
                j += 1
            canvas.delete(self.aliens_fleet[i].get_id())
            i += 1
        self.aliens_fleet.clear()

    def get_number_of_aliens_alive(self):  # Récupère le nombre d'alien vivant
        ret = 0
        for alien in self.aliens_fleet:
            if alien.get_alive():
                ret += 1
        return ret

    def get_width(self):  # Accesseurs width (la largeur de la flotte)
        return (self.aliens_columns * 50) + \
            ((self.aliens_columns - 1) * self.aliens_inner_gap)

    def get_height(self):  # Accesseurs height (la hauteur de la flotte)
        return (self.aliens_lines * 45) + \
            ((self.aliens_lines - 1) * self.aliens_inner_gap)

    def get_alien_x_delta(self):  # Accesseurs alien_x_delta (la direction sur l'axe x)
        return self.alien_x_delta

    def set_alien_x_delta(self, alien_x_delta):  # Change la direction sur l'axe x
        self.alien_x_delta = alien_x_delta

    def get_alien_y_delta(self):  # Accesseurs alien_y_delta (la direction sur l'axe y)
        return self.alien_y_delta

    def set_alien_y_delta(self, alien_y_delta):  # Change la direction sur l'axe y
        self.alien_y_delta = alien_y_delta

    # Accesseurs expl_and_lifetime (le dictionnaire des explosions et leur
    # temps de vie)
    def get_expl_and_lifetime(self):
        return self.expl_and_lifetime

    # Accesseurs aliens_fleet (la liste des aliens de la flotte)
    def get_aliens_fleet(self):
        return self.aliens_fleet

#--------------------------------------------------------------Runtime--------------------------------------------------------------#


SpaceInvaders().play()  # Lance le jeu
