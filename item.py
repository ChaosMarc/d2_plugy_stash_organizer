from bit_utils import read_bits, write_bits
from item_data import get_item_type, get_item_size_x, get_item_size_y, get_set_id, get_unique_name, ItemQuality, ItemVersion


# Item class, holding the various relevant item-related attributes and methods
class Item:
    def __init__(self, data):
        self.data = data  # The byte data

        offset = 20
        self.is_identified, offset = self.read_attribute(data, offset, 1)  # offset: 20
        offset += 6  # unknown bits
        self.is_socketed, offset = self.read_attribute(data, offset, 1)  # offset: 27
        offset += 1  # unknown bits
        offset += 1  # irrelevant bit: is_new
        offset += 2  # unknown bits
        self.is_ear, offset = self.read_attribute(data, offset, 1)  # offset: 32
        offset += 1  # irrelevant bit: is_starter_item
        offset += 3  # unknown bits
        self.is_simple, offset = self.read_attribute(data, offset, 1)  # offset: 37
        self.is_ethereal, offset = self.read_attribute(data, offset, 1)  # offset: 38
        offset += 1  # unknown bit
        self.is_personalized, offset = self.read_attribute(data, offset, 1)  # offset: 40
        offset += 1  # unknown bit
        self.is_runeword, offset = self.read_attribute(data, offset, 1)  # offset: 42
        offset += 5  # unknown bits
        self.version, offset = self.read_version(self, offset, 8)  # offset: 48
        offset += 2  # unknown bits
        offset += 3  # irrelevant bits: location_id
        offset += 4  # irrelevant bits: equipped_id
        offset += 4  # irrelevant bits: position_x
        offset += 3  # irrelevant bits: position_y
        offset += 1  # unknown bit
        offset += 3  # irrelevant bits: alt_position_id

        if self.is_ear == 1:
            self.ear_class, offset = self.read_attribute(data, offset, 3)  # offset: 76
            self.ear_level, offset = self.read_attribute(data, offset, 7)  # offset: 79
            self.ear_data, offset = self.read_attribute_as_char(data, offset, 15, 7)  # offset: 86
        else:
            self.code, offset = self.read_attribute_as_char(data, offset, 4, 8)  # offset: 76
            self.type = get_item_type(self.code)
            self.num_filled_sockets, offset = self.read_attribute(data, offset, 3)  # offset: 108

        if self.is_simple == 1:
            self.quality = None
        else:
            self.identifier, offset = self.read_attribute(data, offset, 32)  # offset: 111
            self.level, offset = self.read_attribute(data, offset, 7)  # offset: 143
            self.quality, offset = self.read_quality(self, offset, 4)  # offset: 150

            self.has_multiple_pictures, offset = self.read_attribute(data, offset, 1)  # offset: 154
            if self.has_multiple_pictures == 1:
                self.picture_id, offset = self.read_attribute(data, offset, 3)

            self.is_class_specific, offset = self.read_attribute(data, offset, 1)
            if self.is_class_specific == 1:
                self.class_specific_data, offset = self.read_attribute(data, offset, 11)

            if self.quality in (ItemQuality.LOW_QUALITY, ItemQuality.HIGH_QUALITY):
                offset += 3  # irrelevant bits
            elif self.quality == ItemQuality.MAGIC:
                self.prefix_id, offset = self.read_attribute(data, offset, 11)
                self.suffix_id, offset = self.read_attribute(data, offset, 11)
            elif self.quality == ItemQuality.SET:
                self.set_item_id, offset = self.read_attribute(data, offset, 12)
                self.set_id = get_set_id(self.set_item_id)
            elif self.quality == ItemQuality.UNIQUE:
                self.unique_id, offset = self.read_attribute(data, offset, 12)
                self.unique_name = get_unique_name(self.unique_id)
            elif self.quality in (ItemQuality.RARE, ItemQuality.CRAFTED):
                offset += 0  # TODO parseRareOrCraftedBits

            if self.is_runeword == 1:
                offset += 16  # TODO parseRunewordBits

            if self.is_personalized == 1:
                self.personalized_data, offset = self.read_attribute_as_char(data, offset, 15, 7)

            # TODO further parsing

        self.x_size = get_item_size_x(self.code)  # How many horizontal slots does the item take
        self.y_size = get_item_size_y(self.code)  # How many vertical slots does the item take

    @staticmethod
    def read_attribute(item, offset, bits_to_read):
        return read_bits(item, offset, bits_to_read), offset + bits_to_read

    @staticmethod
    def read_version(self, offset, bits_to_read):
        version_id, _ = self.read_attribute(self.data, offset, bits_to_read)
        return ItemVersion(version_id), offset + bits_to_read

    @staticmethod
    def read_quality(self, offset, bits_to_read):
        quality_id, _ = self.read_attribute(self.data, offset, bits_to_read)
        return ItemQuality(quality_id), offset + bits_to_read

    @staticmethod
    def read_attribute_as_char(item, offset, char_count, bits_per_char):
        item_code = ''
        for _ in range(char_count):  # Reach each char individually
            char = chr(read_bits(item, offset, bits_per_char))
            offset += bits_per_char
            if char == ' ':
                break
            item_code += char
        return item_code, offset

    def set_position(self, x, y):
        # Modify item data and write new stash position
        self.data = write_bits(self.data, 65, 4, x)
        self.data = write_bits(self.data, 69, 4, y)
