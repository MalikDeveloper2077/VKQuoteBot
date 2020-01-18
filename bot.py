import random
import os

from PIL import Image, ImageDraw, ImageFont
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

import constants


# Settings
vk_session = vk_api.VkApi(token=constants.API_KEY)
long_poll = VkLongPoll(vk_session)
vk = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)


class Quoter:
    """Quoter does the quotes with user text + random image"""
    _images = constants.IMAGES_FOR_QUOTES
    _fonts = constants.FONTS_FOR_QUOTES

    def __new__(cls, *args, **kwargs):
        """Quoter must have only 1 object"""
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def take_photo(self, text):
        """Take random photo_path from _images and write the text.

        Calculate the average coordinates of the picture. Use the quote_text_update method.
        Insert \n in the returned text_list in the join method to get string.
        Write that text on the image. Save it in user_images / and return the uploaded photo

        """
        photo_path = random.choice(self._images)
        image = Image.open(photo_path)
        quote_image = ImageDraw.Draw(image)

        font_size = 65
        font = ImageFont.truetype(random.choice(self._fonts), font_size)

        upd_text = self.quote_text_update(text)
        longest_line = max(upd_text)

        text_width, text_height = font.getsize(longest_line)
        text_height *= len(upd_text)
        real_text = "\n".join(upd_text)

        x = 1 * image.size[0] / 2 - 1 * text_width / 2
        y = 1 * image.size[1] / 2 - 1 * text_height / 2

        quote_image.text(xy=(x, y), text=real_text, font=font, fill=(255, 255, 255))

        new_user_image_path = f'user_images/draw{random.randint(1, 9999999)}.png'
        image.save(new_user_image_path)

        return upload.photo_messages(photos=new_user_image_path)[0]

    @staticmethod
    def quote_text_update(text):
        """If length of text > 2 -> split it for 3 words and return as list"""
        word_lst = []
        option = ''
        count = 0
        txt_lst = text.split(' ')

        if len(txt_lst) > 2:
            for word in txt_lst:
                option += word + ' '
                count += 1
                if count == 2:
                    word_lst.append(option)
                    option = ''
                    count = 0
            else:
                word_lst.append(option)
            return word_lst
        else:
            return [text]

    @staticmethod
    def remove_photo():
        """Get all user_images paths and delete them"""
        folder = []
        paths = []

        for i in os.walk('test'):
            folder.append(i)

        for address, dirs, files in os.walk('user_images'):
            for file in files:
                paths.append(file)

        for path in paths:
            os.remove(f'user_images/{path}')


def main():
    """Event loop and send message"""
    quoter = Quoter()

    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            photo = quoter.take_photo(event.text)
            quoter.remove_photo()

            vk.messages.send(
                user_id=event.user_id,
                message='Держи, брат.',
                attachment=f'photo{photo["owner_id"]}_{photo["id"]}',
                random_id=random.randint(1, 21212212121)
            )
        elif event.type == VkEventType.MESSAGE_NEW and event.to_me and not event.text:
            vk.messages.send(
                user_id=event.user_id,
                message='Брат, напиши мне текст.',
                random_id=random.randint(1, 21212212121)
            )


if __name__ == '__main__':
    main()

