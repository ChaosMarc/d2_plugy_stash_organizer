from bit_utils import read_bits, write_bits
from item_data import get_item_group, get_item_size_x, get_item_size_y, get_true_set_id, Rarity, Version


# Item class, holding the various relevant item-related attributes and methods
class Item:
    def __init__(self, data):
        self.data = data  # The byte data
        self.code = self.get_item_code(data)        # Item code, i.e. "amu", "rng" etc
        self.rw = self.is_runeword(data)            # Is the item a runeword?
        self.simple = self.is_simple(data)          # Is the item "simple" (contains limited amount of data)
        self.rarity = self.get_rarity(data)         # Item rarity (normal, unique, rare, etc)
        self.identifier = self.get_identifier(data) # Unique item identifier (used for dupe checks)
        self.level = self.get_level(data)           # Item level
        self.unique_id = self.get_unique_id(data)   # Which set does item belong to?
        self.set_id = self.get_set_id(data)         # Which set does item belong to?
        self.group = get_item_group(self.code)      # What group does the item belong to (gloves, jewel, uber key, etc)
        self.x_size = get_item_size_x(self.code)    # How many horizontal slots does the item take
        self.y_size = get_item_size_y(self.code)    # How many vertical slots does the item take

    def set_position(self, x, y):
        # Modify item data and write new stash position
        self.data = write_bits(self.data, 65, 4, x)
        self.data = write_bits(self.data, 69, 4, y)

    @staticmethod
    def get_position(item):
        # Get position in stash
        x_pos = read_bits(item, 65, 4)
        y_pos = read_bits(item, 69, 4)
        return x_pos, y_pos

    @staticmethod
    def get_item_code(item):
        # Get the item code
        if Item.is_ear(item):  # Ears lack the bits that indicate item code, but they have a specific ear indicator
            return 'ear'
        item_code = ''
        for i in range(4):  # Reach each char individually
            char = chr(read_bits(item, 76 + i * 8, 8))
            if char != ' ':  # Item codes are 4 bytes long but most of them have a space as the last char which
                # should be ignored
                item_code += char
        return item_code

    @staticmethod
    def is_identified(item):
        return read_bits(item, 20, 1)

    @staticmethod
    def is_socketed(item):
        return read_bits(item, 27, 1)

    @staticmethod
    def is_ear(item):
        return read_bits(item, 32, 1)

    @staticmethod
    def is_simple(item):
        return read_bits(item, 37, 1)

    @staticmethod
    def is_ethereal(item):
        return read_bits(item, 38, 1)

    @staticmethod
    def is_personalized(item):
        return read_bits(item, 40, 1)

    @staticmethod
    def is_runeword(item):
        return read_bits(item, 42, 1)

    @staticmethod
    def get_version(item):
        return Version(read_bits(item, 48, 8))

    @staticmethod
    def num_filled_sockets(item):
        # Return number of socketed items in item
        if Item.is_ear(item):
            return 0
        return read_bits(item, 108, 3)

    @staticmethod
    def get_identifier(item):
        if Item.is_simple(item):
            return None
        return read_bits(item, 111, 32))

    @staticmethod
    def get_level(item):
        if Item.is_simple(item):
            return None
        return Rarity(read_bits(item, 143, 7))

    @staticmethod
    def get_rarity(item):
        if Item.is_simple(item):
            return None
        return Rarity(read_bits(item, 150, 4))

    @staticmethod
    def has_multiple_pictures(item):
        # Used to indicate whether an item can have multiple graphics (like rings, amulets, jewels etc)
        return read_bits(item, 154, 1)

    @staticmethod
    def is_class_specific(item):
        # The bits indicating if an item is class specific vary in location based on whether it has multiple pictures
        offset = 155
        if Item.has_multiple_pictures(item):
            offset += 1
        return read_bits(item, offset, 1)

    def get_unique_id(self, item):
        if self.rarity is not Rarity.UNIQ:  # First, make sure it's actually a unique item
            return None
        offset = 156
        if self.has_multiple_pictures(item):
            offset += 3
        if self.is_class_specific(item):
            offset += 11
        return read_bits(item, offset, 12)

    def get_set_id(self, item):
        # Get the set id of the item.
        if self.rarity is not Rarity.SET:  # First, make sure it's actually a set item
            return None
        # The relevant bit offset depends on whether the item has multiple graphics and/or is class specific
        offset = 156
        if self.has_multiple_pictures(item):
            offset += 3
        if self.is_class_specific(item):
            offset += 11
        # Once the set id is obtained, get the "true" set id from item_data.py
        # The set id as given in the item data actually indicates the specific item and not the set, i.e. Sigon parts
        # have different ids in the 35-40 range, Death's set is 47-49, etc. We want a single id for each set.
        return get_true_set_id(read_bits(item, offset, 12))
