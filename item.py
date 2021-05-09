import item_data
from copy import deepcopy
from bit_utils import read_bits, write_bits, get_data_chunks


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
        self.location_id, offset = self.read_attribute(data, offset, 3)  # offset: 58
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
            self.type = item_data.get_item_data(self.code).type
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

            if self.quality in (item_data.ItemQuality.LOW_QUALITY, item_data.ItemQuality.HIGH_QUALITY):
                offset += 3  # irrelevant bits
            elif self.quality == item_data.ItemQuality.MAGIC:
                self.prefix_id, offset = self.read_attribute(data, offset, 11)
                self.suffix_id, offset = self.read_attribute(data, offset, 11)
            elif self.quality == item_data.ItemQuality.SET:
                self.set_item_id, offset = self.read_attribute(data, offset, 12)
                set_item_data = item_data.get_set_item_data(self.set_item_id)
                self.set_item_name = set_item_data.set_item_name
                self.set_id = set_item_data.set_id
                set_data = item_data.get_set_data(self.set_id)
                self.set_name = set_data.set_name
                self.set_difficulty = set_data.difficulty
            elif self.quality == item_data.ItemQuality.UNIQUE:
                self.unique_id, offset = self.read_attribute(data, offset, 12)
                self.unique_name = item_data.get_unique_name(self.unique_id)
            elif self.quality in (item_data.ItemQuality.RARE, item_data.ItemQuality.CRAFTED):
                self.rare_name_id1, offset = self.read_attribute(data, offset, 8)
                self.rare_name1 = item_data.get_rare_name(self.rare_name_id1)
                self.rare_name_id2, offset = self.read_attribute(data, offset, 8)
                self.rare_name2 = item_data.get_rare_name(self.rare_name_id2)
                self.prefix_ids = []
                self.suffix_ids = []
                for i in range(6):
                    has_pre_or_suffix, offset = self.read_attribute(data, offset, 1)
                    if has_pre_or_suffix == 1:
                        pre_or_suffix_id, offset = self.read_attribute(data, offset, 11)
                        if (i % 2) == 0:
                            self.prefix_ids.append(pre_or_suffix_id)
                        else:
                            self.suffix_ids.append(pre_or_suffix_id)

            if self.is_runeword == 1:
                self.runeword_id, offset = self.read_attribute(data, offset, 12)
                self.runeword_name = item_data.get_runeword_name(self.runeword_id)
                offset += 4  # unknown bits

            if self.is_personalized == 1:
                self.personalized_data, offset = self.read_attribute_as_char(data, offset, 15, 7)

            if self.is_tome():  # Tomes
                offset += 5  # unknown bits

            self.timestamp, offset = self.read_attribute(data, offset, 1)

            if self.is_armor() or self.is_shield():
                self.defense, offset = self.read_attribute(data, offset, 11)
                self.defense -= 10  # for an unknown reason this has to be subtracted

            if self.is_armor() or self.is_shield() or self.is_weapon():
                self.max_durability, offset = self.read_attribute(data, offset, 8)
                if self.max_durability > 0:
                    self.durability, offset = self.read_attribute(data, offset, 8)
                    offset += 1  # unknown bit

            if self.is_stackable():
                self.quantity, offset = self.read_attribute(data, offset, 9)

            if self.is_socketed:
                self.num_total_sockets, offset = self.read_attribute(data, offset, 4)

            set_list_count_value = 0
            if self.quality == item_data.ItemQuality.SET:
                set_list_count_value, offset = self.read_attribute(data, offset, 5)
                self.set_list_count = item_data.get_set_list_count(set_list_count_value)

            offset, properties = self.read_magic_properties(self, offset)
            self.magic_properties = properties

            self.set_properties = {}
            if self.quality == item_data.ItemQuality.SET and self.set_list_count > 0:
                for i in range(self.set_list_count):
                    offset, properties = self.read_magic_properties(self, offset)
                    self.set_properties = self.merge_properties_dicts(self.set_properties, properties)
                if self.set_id == 0 and self.set_item_id == 0:  # Civerb's Ward
                    self.set_attributes_ids_req = [1, 2]
                else:
                    self.set_attributes_num_req = []
                    for i in range(4):
                        if set_list_count_value & (1 << i) == 0:
                            continue
                        self.set_attributes_num_req.append(i + 2)

            self.runeword_properties = {}
            if self.is_runeword == 1:
                offset, properties = self.read_magic_properties(self, offset)
                self.runeword_properties = properties

            chunks = get_data_chunks(self.data, b'JM')[1:]  # socketable items are appended after the actual item
            self.socketables = []
            self.socketable_properties = {}
            for chunk in chunks:
                item_in_socket = Item(chunk)
                socketable_item_data = item_data.get_socketable_item_data(item_in_socket.code)
                if socketable_item_data is not None:
                    item_in_socket.name = socketable_item_data.name
                    if self.is_weapon():
                        item_in_socket.magic_properties = socketable_item_data.weapon_properties
                    elif self.is_armor():
                        item_in_socket.magic_properties = socketable_item_data.armor_properties
                    elif self.is_shield():
                        item_in_socket.magic_properties = socketable_item_data.shield_properties
                    item_in_socket.translated_magic_properties = self.translate_properties(item_in_socket.magic_properties)
                self.socketables.append(item_in_socket)

            self.all_properties = self.merge_properties_dicts({}, self.magic_properties)
            self.all_properties = self.merge_properties_dicts(self.all_properties, self.set_properties)
            self.all_properties = self.merge_properties_dicts(self.all_properties, self.runeword_properties)
            self.socketable_properties = {}
            for socketable in self.socketables:
                self.socketable_properties = self.merge_properties_dicts(self.socketable_properties, socketable.magic_properties)
            self.all_properties = self.merge_properties_dicts(self.all_properties, self.socketable_properties)

            self.translated_magic_properties = self.translate_properties(self.magic_properties)
            self.translated_set_properties = self.translate_properties(self.set_properties)
            self.translated_runeword_properties = self.translate_properties(self.runeword_properties)
            self.translated_socketable_properties = self.translate_properties(self.socketable_properties)
            self.translated_all_properties = self.translate_properties(self.all_properties)

        self.x_size = item_data.get_item_size_x(self.code)  # How many horizontal slots does the item take
        self.y_size = item_data.get_item_size_y(self.code)  # How many vertical slots does the item take


    @staticmethod
    def translate_properties(properties):
        props = deepcopy(properties)
        translated_properties = []
        for prop_id in props:
            if 195 <= prop_id <= 203:
                props[prop_id][1] = item_data.get_skill_name(props[prop_id][1])
            if 214 <= prop_id <= 250:
                props[prop_id][0] = props[prop_id][0] / 8
            if 252 <= prop_id <= 253:
                props[prop_id][0] = 100 / props[prop_id][0]
            # TODO handle all other special cases. see comments in magic_properties and https://github.com/nokka/d2s/blob/master/item.go
            translated_properties.append(item_data.get_magic_property(prop_id).name.format(*props[prop_id]))
        return translated_properties

    @staticmethod
    def merge_properties_dicts(dict1, dict2):
        for key in dict2.keys():
            if key not in dict1:
                dict1[key] = dict2[key]
            else:
                dict1[key] = [x + y for x, y in zip(dict1[key], dict2[key])]
        return dict1

    @staticmethod
    def read_attribute(item, offset, bits_to_read):
        return read_bits(item, offset, bits_to_read), offset + bits_to_read

    @staticmethod
    def read_version(self, offset, bits_to_read):
        version_id, _ = self.read_attribute(self.data, offset, bits_to_read)
        return item_data.ItemVersion(version_id), offset + bits_to_read

    @staticmethod
    def read_quality(self, offset, bits_to_read):
        quality_id, _ = self.read_attribute(self.data, offset, bits_to_read)
        return item_data.ItemQuality(quality_id), offset + bits_to_read

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

    @staticmethod
    def read_magic_properties(self, offset):
        properties = {}
        while True:
            try:
                property_id, offset = self.read_attribute(self.data, offset, 9)
            except IndexError:
                # not sure what is appended after some items but all visible properties are read correctly
                break
            if property_id == 511:
                break
            magic_property = item_data.get_magic_property(property_id)
            values = []
            for bit_length in magic_property.bits:
                property_value, offset = self.read_attribute(self.data, offset, bit_length)
                values.append(property_value - magic_property.bias)
            properties[property_id] = values
        return offset, properties

    def set_position(self, x, y):
        # Modify item data and write new stash position
        self.data = write_bits(self.data, 65, 4, x)
        self.data = write_bits(self.data, 69, 4, y)

    def is_stackable(self):
        return self.type in [item_data.ItemType.THROW, item_data.ItemType.THROWPOT, item_data.ItemType.JAV] or \
               self.code in ["am5", "ama", "amf", "key", "aqv", "cqv"] or \
               self.is_tome()

    def is_tome(self):
        return self.code in ["tkb", "ibk"]

    def is_armor(self):
        return self.type in [item_data.ItemType.BARB, item_data.ItemType.BELT, item_data.ItemType.BODY, item_data.ItemType.BODY, item_data.ItemType.BOOTS, item_data.ItemType.CIRCLET,
                             item_data.ItemType.GLOVES, item_data.ItemType.HELM, item_data.ItemType.PELT]

    def is_shield(self):
        return self.type in [item_data.ItemType.NEC, item_data.ItemType.PAL, item_data.ItemType.SHIELD]

    def is_weapon(self):
        return self.type in [item_data.ItemType.AMA, item_data.ItemType.ASN, item_data.ItemType.AXE, item_data.ItemType.BOW, item_data.ItemType.DAGGER, item_data.ItemType.JAV, item_data.ItemType.MACE,
                             item_data.ItemType.POLEARM, item_data.ItemType.SCEPTER, item_data.ItemType.SORC, item_data.ItemType.SPEAR, item_data.ItemType.STAFF, item_data.ItemType.SWORD,
                             item_data.ItemType.THROW, item_data.ItemType.WAND, item_data.ItemType.XBOW]

    def __str__(self):
        arr = [self.type, self.quality, item_data.get_item_data(self.code).name]
        if self.is_simple == 0:
            arr.append(self.level)
            if self.quality == item_data.ItemQuality.SET:
                arr.append(self.set_name)
                arr.append(self.set_item_name)
            if self.quality == item_data.ItemQuality.UNIQUE:
                arr.append(self.unique_name)
            if self.is_socketed:
                arr.append('/'.join(str(i) for i in [self.num_filled_sockets, self.num_total_sockets]))
                socketables = []
                for socketable in self.socketables:
                    socketables.append(item_data.get_item_data(socketable.code).name)
                arr.append("[" + ', '.join(socketables) + "]")
            if self.is_runeword == 1:
                arr.append(self.runeword_name)
            arr.append("[" + ', '.join(self.translated_all_properties) + "]")
        return ', '.join(str(i) for i in arr)
