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
        Write that text on the image. Save it in user_images/ and return the uploaded photo

        """
        photo_path = random.choice(self._images)
        image = Image.open(photo_path)
        image = image.convert('RGB')
        quote_image = ImageDraw.Draw(image)

        # Font
        font_size = 55
        font = ImageFont.truetype(random.choice(self._fonts), font_size)

        # Update text
        upd_text = self.quote_text_update(text)
        longest_line = self.get_longest_line(upd_text)
        end_upd_text = "\n".join(upd_text)
        real_text = self.quotes_replace_in_str(end_upd_text)

        # Coordinates
        text_width, text_height = font.getsize(longest_line)
        text_height *= len(upd_text)

        x = 1 * image.size[0] / 2 - 1 * text_width / 2
        y = 1 * image.size[1] / 2 - 1 * text_height / 2
        if x < 0:
            x = 10
        if y < 0:
            y = 10

        # Write text and save
        quote_image.text(xy=(x, y), text=real_text, font=font, fill=(255, 255, 255))
        new_user_image_path = f'user_images/draw{random.randint(1, 9999999)}.png'
        image.save(new_user_image_path)

        return upload.photo_messages(photos=new_user_image_path)[0]

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

    @staticmethod
    def quote_text_update(text):
        """If text length > 3 cut it by 3 words and return as list.
        Else return given text as list
        """
        word_lst = []
        option = ''
        count = 0
        txt_lst = text.split(' ')

        if len(txt_lst) > 3:
            for word in txt_lst:
                option += word + ' '
                count += 1
                if count == 3:
                    word_lst.append(option)
                    option = ''
                    count = 0
            else:
                word_lst.append(option)
            return word_lst
        else:
            return [text]

    def get_longest_line(self, line_lst):
        """Return the longest line of line list"""
        longest_line = ''
        if len(line_lst) > 1:
            max_count = 0

            for line in line_lst:
                replaced_line = self.quotes_replace_in_str(line)
                count = 0
                for char in replaced_line:
                    count += 1
                if count > max_count:
                    max_count = count
                    longest_line = replaced_line
        else:
            longest_line = self.quotes_replace_in_str(line_lst[0])

        return longest_line

    @staticmethod
    def quotes_replace_in_str(string):
        """Replace quotation marks symbols in a str with << and >>"""
        replaced_str = string.replace('&quot;', '"')
        return replaced_str


def main():
    """Event loop and send message.

    If the user sends a message to the bot, check.
    If the text length is < 160, take a random photo using quote.take_photo(text) and send a message.
    Else send a message using text and img, where it says "too big text"

    """
    quoter = Quoter()

    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if len(event.text) < 160:
                photo = quoter.take_photo(event.text)
                quoter.remove_photo()

                try:
                    vk.messages.send(
                        user_id=event.user_id,
                        message='Держи, брат.',
                        attachment=f'photo{photo["owner_id"]}_{photo["id"]}',
                        random_id=random.randint(1, 21212212121)
                    )
                except vk_api.exceptions.ApiError:
                    pass
            else:
                img_for_big_text = upload.photo_messages(photos='images/for_big_text.jpg')[0]

                try:
                    vk.messages.send(
                        user_id=event.user_id,
                        message='Брат, слишком много текста. Брат, по-братски, давай поменьше.',
                        attachment=f'photo{img_for_big_text["owner_id"]}_{img_for_big_text["id"]}',
                        random_id=random.randint(1, 21212212121)
                    )
                except vk_api.exceptions.ApiError:
                    pass

        elif event.type == VkEventType.MESSAGE_NEW and event.to_me and not event.text:
            try:
                vk.messages.send(
                    user_id=event.user_id,
                    message='Брат, напиши мне текст.',
                    random_id=random.randint(1, 21212212121)
                )
            except vk_api.exceptions.ApiError:
                pass


if __name__ == '__main__':
    main()
