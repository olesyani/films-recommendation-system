import requests
from io import BytesIO
from tkinter import *
from PIL import ImageTk, Image

import main


class FilmsFrame:

    def __init__(
            self,
            window,
            desc='Здесь должно быть краткое описание фильма',
            lbl='Название фильма',
            pic='https://image.winudf.com/v2/image/Y29tLnR1bWVyYi5tYXRyaXhsb2NrX3NjcmVlbl8wXzE1MzA5MDU1NTZfMDk2/screen-0.jpg?fakeurl=1&type=.webp'
    ):
        self.poster_img = self.pic_modification(pic)

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
        # когда будет добавлена бд, будет отмечаться, что фильм понравился
        # так же решаю проблему с тем, чтобы фильм обновлялся
        return

    def do_not_like_film(self):
        # когда будет добавлена бд, будет отмечаться, что фильм не понравился
        # так же решаю проблему с тем, чтобы фильм обновлялся
        return

    def rename(self, desc, lbl, pic):
        self.poster_img = self.pic_modification(pic)
        self.film_title['text'] = lbl
        self.description['text'] = desc
        self.film_img['image'] = self.poster_img

    def pic_modification(self, link):
        response = requests.get(link)
        img = Image.open(BytesIO(response.content))
        img_resized = img.resize((180, 260), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img_resized)


class MyGUI:

    def __init__(self):
        self.__mainWindow = Tk()
        self.__mainWindow.title('Помощник по подбору фильмов')
        self.__mainWindow.geometry("500x220")
        self.id_label = Label(self.__mainWindow, text='Введите свой VK ID')
        self.id_entry = Entry(bd=3)
        self.id_label.place(x=70, y=70)
        self.id_entry.place(x=220, y=70)
        self.continue_button = Button(self.__mainWindow, text='Продолжить', command=self.next)
        self.continue_button.place(x=200, y=140)
        self.labelText = ''
        self.helping_labels = Label(self.__mainWindow, text=self.labelText, fg="red")
        self.helping_labels.place(x=220, y=100)
        self.entry_value = ''
        mainloop()

    def next(self):
        v = self.id_entry.get()

        if len(v) == 0:
            print('The entry is empty')
            self.helping_labels['text'] = 'Поле пустое'
            return

        if v != self.entry_value:
            recommendations = main.start(v)
            self.create_recommendations_page(recommendations)
            self.entry_value = v
        else:
            p.deiconify()
            self.__mainWindow.withdraw()

    def create_recommendations_page(self, recs):
        self.__mainWindow.withdraw()

        global p
        p = Toplevel(self.__mainWindow)
        p.title("Помощник по подбору фильмов")

        label_frame = Label(p, text="Рекомендации", font=('Baskerville', 22))
        label_frame.pack(fill=Y, side=TOP, ipady=5)
        label_frame = Label(p, text="для " + self.entry_value, font=('Baskerville', 18))
        label_frame.pack(fill=Y, side=TOP, ipady=15)

        bottom_frame = Frame(p, height=50)
        bottom_frame.pack(side=BOTTOM, ipady=5)
        back_button = Button(bottom_frame, text='Назад', command=self.back)
        back_button.pack()

        for i in range(4):
            FilmsFrame(p, desc=recs[i]['description'], lbl=recs[i]['title'], pic=recs[i]['image'])

    def back(self):
        self.__mainWindow.deiconify()
        p.withdraw()


myGUI = MyGUI()