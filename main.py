import threading
from functools import partial
import PIL.Image

from kivy import clock, Config
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import mainthread
from kivy.factory import Factory
from kivy.graphics.context_instructions import PushMatrix, PopMatrix, Rotate
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition, SlideTransition
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, Clock
from kivy.utils import rgba
from CompareSum import main_function
from simple_image_download import simple_image_download as simp
import webbrowser
from kivy.core.window import Window
from itertools import cycle
import certifi
import os

#os.environ['KIVY_METRICS_DENSITY'] = '1'
os.environ['SSL_CERT_FILE'] = certifi.where()

__version__ = '1.0'


class WindowManager(ScreenManager):
    MOST_MENTIONED = ObjectProperty()
    TOP_RATED = ObjectProperty()
    PRODUCTS = ObjectProperty()

    PRODUCT_TITLE = StringProperty('')
    NUM_SITES = NumericProperty()
    DF_STR = StringProperty()

    def main_alg(self):
        self.MOST_MENTIONED, self.TOP_RATED, self.PRODUCTS = main_function(self.ids.main_screen.input_string)


class OpenScreen(Screen):

    def trans(self, *args):
        self.manager.transition = FadeTransition()
        self.manager.current = 'main'
        self.manager.transition = SlideTransition()

    def on_enter(self, *args):
        self.add_widget(Image(source='option 2.png', size_hint=(1.05,1.05)))
        Clock.schedule_once(self.trans, 4)


class MainScreen(Screen):
    input_string = StringProperty('')

    def update_input_string(self):
        self.input_string = self.ids.input_string.text

    stop = threading.Event()

    def start_second_thread(self):
        threading.Thread(target=self.second_thread).start()

    def algorithm(self, *args):

        self.update_input_string()
        self.manager.main_alg()

    def second_thread(self):

        Clock.schedule_once(self.animations, 0)
        self.algorithm()
        self.next_screen()

    def add_label(self, dt):

        label = Label(text='Are you excited?\nBeacuse I do!', font_name='Ubuntu-C.ttf', color=[0,0,0,1],
              size_hint=(0.8, 0.2),valign='center', halign='center', pos_hint={"x":0.1, "y":0}, font_size=self.width/10)

        self.manager.ids.loading_screen.add_widget(label)
        Clock.schedule_once(lambda d: self.manager.ids.loading_screen.remove_widget(label), 5)




    @mainthread
    def animations(self, dt):
        self.manager.current = 'loading'

        anim_big = Animation(angle=10800, duration=250)
        anim_small = Animation(angle=-10800, duration=500)

        anim_big.start(self.manager.ids.loading_screen.ids.big)
        anim_small.start(self.manager.ids.loading_screen.ids.small)

        Clock.schedule_once(self.add_label, 5)

    @mainthread
    def next_screen(self):
        self.manager.current = 'results'


class LoadingScreen(Screen):
    pass


class ResultsScreen(Screen):
    input_string = StringProperty()

    stop = threading.Event()

    def start_second_thread(self, product, *args):
        threading.Thread(target=partial(self.second_thread,product)).start()

    def product_page(self, product, *args):
        self.manager.PRODUCT_TITLE = product
        response = simp.simple_image_download

        try:
            response().download(product, 1)
            image = PIL.Image.open(f"simple_images/{product}/{product}_1.jpg")
        except PIL.UnidentifiedImageError:
            response().download(product, 2)
            image = PIL.Image.open(f"simple_images/{product}/{product}_2.jpg")

        image.save("product.jpg")
        self.manager.ids.product_screen.img.reload()

    def second_thread(self,product):
        Clock.schedule_once(self.animation,0)
        self.product_page(product)
        self.next_screen()

    @mainthread
    def animation(self, dt):

        anim_big = Animation(angle=10800, duration=250)
        anim_big &= Animation(opacity=1, duration=0.2)
        anim_small = Animation(angle=-10800, duration=500)
        anim_small &= Animation(opacity=1, duration=0.2)

        anim_big.start(self.manager.ids.results_screen.ids.big)
        anim_small.start(self.manager.ids.results_screen.ids.small)


    @mainthread
    def next_screen(self):

        self.manager.ids.results_screen.ids.big.opacity = 0
        self.manager.ids.results_screen.ids.small.opacity = 0
        self.manager.current = 'product'


    def update_results(self, df_str):

        self.ids.grid.clear_widgets()

        if df_str == 'Most Mentioned':
            df = self.manager.MOST_MENTIONED
            i = 0
            for product in df['title'].iloc[0:10]:
                sites_occur = df.loc[df['title'] == product]['sites_occur'].values[0]
                button = Button(text=f"\n\n[b]{product}[/b]\n\n Appeared in {str(sites_occur)} sites",
                                background_normal=f'{i + 1}.png', background_down=f'{i + 1}_dark.png',
                                font_name='Ubuntu-C.ttf', font_size=80, color=[0, 0, 0, 1], size=(900, 900),
                                size_hint=(None, None), halign='center', valign='center', markup=True, id=product)
                button.bind(on_release=partial(self.start_second_thread, product))
                self.ids.grid.add_widget(button)
                i += 1
            self.manager.DF_STR = 'Most Mentioned'

        elif df_str == 'Top Rated':

            if self.manager.TOP_RATED.iloc[0]['num_sites'] < 3:
                # popup = Popup()
                # self.add_widget(popup)
                #
                # # def dismiss_popup(popup, dt):
                # #     popup.dismiss()
                #
                # Clock.schedule_once(popup.dismiss, 1)
                pass



            else:
                df = self.manager.TOP_RATED
                i = 0
                for product in df['title'].iloc[0:10]:
                    weighted_average = round(df.loc[df['title'] == product]['weighted_average'].values[0], 2)
                    num_sites = df.loc[df['title'] == product]['num_sites'].values[0]
                    button = Button(text=f"\n\n[b]{product}[/b]\n\n{str(weighted_average)} out of {str(num_sites)} sites",
                                    background_normal=f'{i + 1}.png', background_down=f'{i + 1}_dark.png',
                                    font_name='Ubuntu-C.ttf', font_size=80, color=[0, 0, 0, 1], size=(900, 900),
                                    size_hint=(None, None), halign='center', valign='center', markup=True)
                    button.bind(on_release=partial(self.start_second_thread, product))
                    self.ids.grid.add_widget(button)
                    i += 1
                self.manager.DF_STR = 'Top Rated'

    def on_pre_enter(self, *args):
        self.input_string = self.manager.ids.main_screen.input_string

        self.update_results('Most Mentioned')


class ProductScreen(Screen):
    product_title = StringProperty()

    def __init__(self, **kwargs):
        super(ProductScreen, self).__init__(**kwargs)
        self.img = AsyncImage(pos_hint={"x": 0.15, "y": 0.3},
                              size_hint=(0.7, 0.825),
                              source='product.jpg')
        self.add_widget(self.img)

    stop = threading.Event()

    def start_second_thread(self, index, *args):
        threading.Thread(target=partial(self.second_thread, index)).start()

    def get_link(self, index, *args):

        if self.manager.DF_STR == 'Top Rated':
            if index < len(self.manager.PRODUCTS[self.manager.PRODUCT_TITLE].sites):
                webbrowser.open(self.manager.PRODUCTS[self.manager.PRODUCT_TITLE].sites[index])

        elif self.manager.DF_STR == 'Most Mentioned':
            if index < len(self.manager.PRODUCTS[self.manager.PRODUCT_TITLE].sites_occurrence):
                webbrowser.open(self.manager.PRODUCTS[self.manager.PRODUCT_TITLE].sites_occurrence[index])

    def second_thread(self, index):
        Clock.schedule_once(self.animation, 0)
        self.get_link(index)
        self.next_screen()

    @mainthread
    def animation(self, dt):

        #self.manager.ids.product_screen.ids.big.opacity = 1
        #self.manager.ids.product_screen.ids.small.opacity = 1

        # anim_big = Animation(angle=10800, duration=250)
        # anim_big &= Animation(opacity=1, duration=0.2)
        # anim_small = Animation(angle=-10800, duration=500)
        # anim_small &= Animation(opacity=1, duration=0.2)
        #
        # anim_big.start(self.manager.ids.product_screen.ids.big)
        # anim_small.start(self.manager.ids.product_screen.ids.small)
        pass

    @mainthread
    def next_screen(self):

        # self.manager.ids.product_screen.ids.big.opacity = 0
        # self.manager.ids.product_screen.ids.small.opacity = 0
        pass





    def update_sites(self, df_str):

        self.ids.relative.clear_widgets()

        if df_str == 'Most Mentioned':
            df = self.manager.MOST_MENTIONED
            sites_occur = df.loc[df['title'] == self.product_title]['sites_occur'].values[0]
            label = Label(text=f"Appeared in {str(sites_occur)} sites", font_name='Ubuntu-C.ttf',
                          color=[0, 0, 0, 1], size_hint=(0.5, 0.55), pos_hint={"x": 0.25, 'y': 0.23}, font_size=100)
            self.ids.relative.add_widget(label)

        elif df_str == 'Top Rated':
            df = self.manager.TOP_RATED
            weighted_average = round(df.loc[df['title'] == self.product_title]['weighted_average'].values[0], 2)
            num_sites = df.loc[df['title'] == self.product_title]['num_sites'].values[0]
            label = Label(text=f"Average rank is {str(weighted_average)} out of {str(num_sites)} sites",
                          font_name='Ubuntu-C.ttf',
                          color=[0, 0, 0, 1], size_hint=(0.5, 0.55), pos_hint={"x": 0.25, 'y': 0.23}, font_size=80)
            self.ids.relative.add_widget(label)

    def on_pre_enter(self, *args):

        self.product_title = self.manager.PRODUCT_TITLE

        self.update_sites(self.manager.DF_STR)

        def shorten(url):
            url = url.replace('https://', '').replace('http://', '')
            domains = ['.com', '.co.uk', '.fr', '.net', '.co.nz', '.org', '.co.il', 'tv']
            for domain in domains:
                if domain in url:
                    cut_url = url[:url.index(domain) + len(domain)]
                    return cut_url

            return url

        self.ids.grid.clear_widgets()

        product = self.manager.PRODUCTS[self.manager.PRODUCT_TITLE]

        hex_colors = cycle(['ff9999', 'ffc99', 'ffff99', 'ccff99', '99ff99', '99ffcc',
                            '99ffff', '99ccff', '9999ff', 'cc99ff', 'ff99ff', 'ff99cc'])

        if self.manager.DF_STR == 'Top Rated':
            i = 0

            if product.num_sites < 5:
                self.ids.top_edge.opacity = 0
                self.ids.bottom_edge.opacity = 0
            else:
                self.ids.top_edge.opacity = 1
                self.ids.bottom_edge.opacity = 1

            for i in range(0, product.num_sites):
                button = Button(text=shorten(product.sites[i]), font_name='Ubuntu-C.ttf', background_normal='website.png',
                                background_down='website_dark.png', background_color=rgba(f"#{next(hex_colors)}"),
                                font_size=80, color=[0, 0, 0, 1], size=(940,180), size_hint=(None, None), halign='center')
                button.bind(on_release=partial(self.start_second_thread, i))
                i += 1
                self.ids.grid.add_widget(button)

        elif self.manager.DF_STR == 'Most Mentioned':
            i = 0

            if len(product.sites_occurrence) < 5:
                self.ids.top_edge.opacity = 0
                self.ids.bottom_edge.opacity = 0
            else:
                self.ids.top_edge.opacity = 1
                self.ids.bottom_edge.opacity = 1

            for i in range(0, len(product.sites_occurrence)):
                button = Button(text=shorten(product.sites_occurrence[i]), font_name='Ubuntu-C.ttf', background_normal='website.png',
                                background_down='website_dark.png', background_color=rgba(f"#{next(hex_colors)}"),
                                font_size=80, color=[0, 0, 0, 1], size=(940, 180), size_hint=(None, None), halign='center')

                button.bind(on_release=partial(self.start_second_thread, i))
                i += 1
                self.ids.grid.add_widget(button)


Builder.load_file("comparesum_kivy.kv")


class CompareSum(App):
    Window.clearcolor = (1, 1, 1, 1)
    Window.size = (dp(360),dp(656))


    sm = WindowManager()

    def build(self):
        CompareSum.sm.add_widget(OpenScreen(name='open'))
        CompareSum.sm.add_widget(MainScreen(name='main'))
        CompareSum.sm.add_widget(LoadingScreen(name='loading'))
        CompareSum.sm.add_widget(ResultsScreen(name='results'))
        CompareSum.sm.add_widget(ProductScreen(name='product'))

        return CompareSum.sm
        return OpenScreen()


if __name__ == '__main__':
    CompareSum().run()
