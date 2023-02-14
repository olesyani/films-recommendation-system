from io import BytesIO
from tkinter import *
from PIL import ImageTk, Image

import main


class FilmsFrame:
    def __init__(self, window, fid, uid, desc, lbl, pic):
        self.poster_img = self.pic_modification(pic)

        self.uid = uid
        self.fid = fid

        self.film_frame = Frame(window, width=220, height=400)

        self.film_img = Label(self.film_frame, image=self.poster_img)
        self.film_img.image = self.poster_img
        self.film_img.pack(fill=BOTH, side=TOP)

        self.film_title = Label(self.film_frame, wraplength=200, text=lbl, font=('Baskerville', 16))
        self.film_title.pack(fill=Y, side=TOP)

        self.description = Label(self.film_frame, wraplength=180, text=desc, font=('Baskerville', 10))
        self.description.pack(fill=BOTH, side=TOP)

        self.bottom_frame = Frame(self.film_frame, height=50, bg='red')
        self.bottom_frame.pack(side=BOTTOM)
        yes_button = Button(self.bottom_frame, text='✔', command=self.like_film)
        yes_button.pack(side=LEFT)
        no_button = Button(self.bottom_frame, text='✘', command=self.do_not_like_film)
        no_button.pack(side=LEFT)

        self.film_frame.pack(fill=BOTH, side=LEFT, expand=True, ipady=15, ipadx=20)

    def like_film(self):
        main.rate(self.fid, self.uid, True)
        mv = main.next_movie(self.uid)
        if mv is not None:
            self.rename(mv['id'], mv['title'], mv['description'], mv['image'])
        else:
            self.film_frame.destroy()
        return

    def do_not_like_film(self):
        main.rate(self.fid, self.uid, False)
        mv = main.next_movie(self.uid)
        if mv is not None:
            self.rename(mv['id'], mv['title'], mv['description'], mv['image'])
        else:
            self.film_frame.destroy()
        return

    def rename(self, fid, title, desc, pic):
        self.poster_img = self.pic_modification(pic)
        self.fid = fid
        self.film_title['text'] = title
        self.description['text'] = desc
        self.film_img['image'] = self.poster_img

    def pic_modification(self, img):
        img = Image.open(BytesIO(img))
        img_resized = img.resize((180, 260), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img_resized)


class MyGUI:
    def __init__(self):
        self.__mainWindow = Tk()
        self.__mainWindow.title('Помощник по подбору фильмов')
        self.__mainWindow.geometry("500x250")
        self.id_label = Label(self.__mainWindow, text='Введите свой VK ID')
        self.id_entry = Entry(bd=3)
        self.id_label.place(x=70, y=70)
        self.id_entry.place(x=220, y=70)
        self.continue_button = Button(self.__mainWindow, text='Продолжить', command=self.next)
        self.continue_button.place(x=200, y=140)
        self.helping_label = Label(self.__mainWindow, text='', fg="red")
        self.helping_label.place(x=220, y=100)
        self.uid = 0
        self.entry_value = ''
        mainloop()

    def next(self):
        v = self.id_entry.get()

        if len(v) == 0:
            print('The entry is empty')
            self.helping_label['text'] = 'Поле пустое'
            return

        if v != self.entry_value:
            self.helping_label['text'] = ''
            self.entry_value = v
            global tmp
            tmp = Toplevel(self.__mainWindow)
            tmp.title("")
            label = Label(tmp, text="Загружаем рекомендации..")
            label.pack(ipady=25, ipadx=25)
            tmp.after(100, self.recommendation_request)
            tmp.mainloop()
        else:
            p.deiconify()
            self.__mainWindow.withdraw()

    def recommendation_request(self):
        uid, recommendations = main.start(self.entry_value)
        self.uid = uid
        if recommendations != 0:
            self.create_recommendations_page(recommendations)
            tmp.destroy()
        else:
            self.helping_label['text'] = 'Неправильный ID'
            tmp.destroy()

    def create_recommendations_page(self, recs):
        global p
        p = Toplevel(self.__mainWindow)
        p.title("Помощник по подбору фильмов")

        fr = Frame(p)
        label_rec = Label(fr, text="Рекомендации", font=('Baskerville', 22))
        label_rec.pack(fill=Y, side=TOP)
        label_user = Label(fr, text="для " + self.entry_value, font=('Baskerville', 18))
        label_user.pack(fill=Y, side=TOP)
        fr.pack(fill=Y, side=TOP, ipady=5)

        bottom_frame = Frame(p, height=50)
        bottom_frame.pack(side=BOTTOM, ipady=5)
        back_button = Button(bottom_frame, text='Назад', command=self.back)
        back_button.pack()

        for i in range(4):
            FilmsFrame(p,
                       fid=recs[i]['id'],
                       uid=self.uid,
                       desc=recs[i]['description'],
                       lbl=recs[i]['title'],
                       pic=recs[i]['image']
                       )

        self.__mainWindow.withdraw()

    def back(self):
        self.__mainWindow.deiconify()
        p.withdraw()


if __name__ == '__main__':
    main.connect()
    myGUI = MyGUI()
    main.close()