import configparser
import struct
import tkinter as tk
from bit_utils import find_next_null, write_bits, get_data_chunks
from copy import copy
from item import Item
from item_data import ItemType, ItemQuality, GemQuality, get_gem_data_by_code, get_gem_data_by_type_and_quality, gems_types, rune_codes, get_rune_upgrade_recipe
from page import Page
from shutil import copy
from tkinter import filedialog

root = tk.Tk()
root.withdraw()


def read_stash_file(file_path):
    # Read stash file and return header, stash version, shared gold (if applicable), number of pages and the rest of
    # the stash data
    with open(file_path, "rb") as f:
        header = f.read(4)
        ver = f.read(2)
        gold = None

        # There is some difference between versions and shared/personal stash files here. If the stash is a shared stash
        # ("SSS\0") and the version is 02, we need to read 4 bytes into shared gold. If the stash is a personal stash
        # ("CSTM") then we need to read 4 unused junk bytes. Otherwise, skip.
        if header == b'SSS\x00' and ver == b'02':
            gold = f.read(4)
        if header == b'CSTM':
            f.read(4)

        num_pages = struct.unpack('I', f.read(4))[0]
        stash_data = f.read(-1)
    return header, ver, gold, num_pages, stash_data


def get_flags(stash_data, ptr):
    # Check if flags exist by counting past the next null and checking for JM
    next_null = find_next_null(stash_data, ptr)
    if stash_data[next_null + 1: next_null + 3] != b'JM':
        return stash_data[ptr: ptr + 4], ptr + 4  # If flags exist then return them and advance pointer
    return None, ptr


def get_page_name(stash_data, ptr):
    # Return page name
    next_null = find_next_null(stash_data, ptr)
    return stash_data[ptr: next_null], next_null + 1


def chunks_unify_sockets(chunks):
    # For each chunk of data (separated by JM), check the bits to see how many socketed items the item contains
    # If an item contains X filled sockets, then append the next X chunks to it and skip forward
    new_chunks = []
    while chunks:
        item_candidate = chunks.pop(0)
        socketed_items = Item(data=item_candidate).num_filled_sockets
        for _ in range(socketed_items):
            item_candidate += chunks.pop(0)
        new_chunks.append(item_candidate)
    return new_chunks


def get_items(page_data, ptr):
    # Get list of items, paying attention to socketed items
    item_data = page_data[ptr:]
    # Get all "chunks" separated by "JM", then unify chunks by considering whether an item is actually a part of
    # (socketed in) the previous item
    chunks = get_data_chunks(item_data, b'JM')[1:]
    items = chunks_unify_sockets(chunks)
    return items


def get_pages(stash_data):
    # Return stash page data
    return get_data_chunks(stash_data, b'ST')


def parse_stash_data(stash_data, config):
    # Retrieve the pages we do not wish to sort, and parse the list of items in the remaining pages
    stash_pages = get_pages(stash_data)
    num_pages_to_ignore = int(config["GENERAL"]["IgnoreFirstXPages"])

    # If there are fewer pages total than those we wish to ignore, do nothing except return all pages.
    # Otherwise divide into pages to ignore and pages to parse
    if num_pages_to_ignore >= len(stash_pages):
        return stash_pages, []
    pages_to_ignore = stash_pages[0:num_pages_to_ignore]
    pages_to_parse = stash_pages[num_pages_to_ignore:]

    # Parse items in remaining pages
    items = []
    for page in pages_to_parse:
        ptr = 2  # Start 2 bytes in
        flags, ptr = get_flags(page, ptr)  # Get page flags and advance pointer
        stash_page_name, ptr = get_page_name(page, ptr)  # Get page name and advance pointer
        page_items = get_items(page, ptr)  # Get items in page
        for item in page_items:
            items.append(Item(data=item))  # Initialize an Item instance for each item

    return pages_to_ignore, items


def add_to_group(group, item, key=None):
    # Add item to list or appropriate subgroup of dictionary
    if isinstance(group, list):
        group.append(item)
    if isinstance(group, dict):
        if key in group:
            group[key].append(item)
        else:
            group[key] = [item]


def append_supergroup_flat(groups, supergroup):
    # Used to "flatten"/"unify" supergroups (sets, uniques) and then append to groups structure
    flat_group = []
    for item in supergroup:
        flat_group.extend(supergroup[item])
    groups.append(flat_group)


def append_supergroup(groups, supergroup):
    # Used to append each item in supergroup to groups
    for item in supergroup:
        groups.append(supergroup[item])


def upgrade_gems(item_list, qualities_to_cube, keep_at_least):
    # Get gems from item list
    gem_list = list(filter(lambda item: item.is_gem(), item_list))

    # get item list without gems
    item_list = list(filter(lambda item: not item.is_gem(), item_list))

    # Initialize a dictionary with keys [gem_type][gem_quality] with empty lists
    gems = {}
    for gem_type in gems_types:
        gems[gem_type] = {}
        for gem_quality in GemQuality:
            gems[gem_type][gem_quality] = []

    # Add gems to gem dictionary
    for gem in gem_list:
        gems[gem.type][gem.gem_quality].append(gem)

    # Upgrade Gems
    for gem_type in gems_types:
        for gem_quality in qualities_to_cube:
            while len(gems[gem_type][gem_quality]) >= (3 + int(keep_at_least)):
                gems[gem_type][gem_quality].pop()
                gems[gem_type][gem_quality].pop()
                g = gems[gem_type][gem_quality].pop()
                g.gem_quality += 1
                g.set_code(get_gem_data_by_type_and_quality(gem_type, g.gem_quality).code)
                gems[gem_type][g.gem_quality].append(g)

    # Turn the dictionary back into a list
    gem_list = []
    for gem_type in gems_types:
        for gem_quality in GemQuality:
            gem_list.extend(gems[gem_type][gem_quality])

    # Add gems back to item list and return it
    return item_list + gem_list


def upgrade_runes(item_list, runes_to_upgrade, keep_at_least, downgrade_gems, ignore_gems):
    # Get runes from item list
    rune_list = list(filter(lambda item: item.type == ItemType.RUNE, item_list))

    # get item list without runes
    item_list = list(filter(lambda item: item.type != ItemType.RUNE, item_list))

    # Initialize a dictionary with keys [rune_code] with empty lists
    runes = {}
    for rune_code in rune_codes:
        runes[rune_code] = []

    # Add runes to rune dictionary
    for rune in rune_list:
        runes[rune.code].append(rune)

    # Upgrade Runes
    for rune_code in runes_to_upgrade:
        recipe = get_rune_upgrade_recipe(rune_code)
        while len(runes[rune_code]) >= (recipe.amount + int(keep_at_least)) and has_gem_for_rune_upgrade(item_list, recipe.gem_code, downgrade_gems, ignore_gems):
            item_list = remove_gem_for_rune_upgrade(item_list, recipe.gem_code, downgrade_gems, ignore_gems)
            r = None
            for _ in range(recipe.amount):
                r = runes[rune_code].pop()
            r.set_code(recipe.next_rune_code)
            runes[recipe.next_rune_code].append(r)

    # Turn the dictionary back into a list
    rune_list = []
    for rune_code in rune_codes:
        rune_list.extend(runes[rune_code])

    # Add runes back to item list and return it
    return item_list + rune_list


def has_gem_for_rune_upgrade(item_list, gem_code, downgrade_gems, ignore_gems):
    if gem_code is None or ignore_gems == '1':
        return True

    gem_codes_to_check = get_gem_codes_to_check(gem_code, downgrade_gems)
    return len(list(filter(lambda item: item.code in gem_codes_to_check, item_list))) > 0


def downgrade_gem_to(item_list, gem_code_from, gem_code_to):
    gem_data_from = get_gem_data_by_code(gem_code_from)
    while gem_data_from.code != gem_code_to:
        for item in item_list:
            if item.code == gem_data_from.code:
                item_list.remove(item)
                item.gem_quality -= 1
                gem_data_from = get_gem_data_by_type_and_quality(item.type, item.gem_quality)
                item.set_code(gem_data_from.code)
                for _ in range(3):
                    item_list.append(copy(item))
                break
    return item_list


def get_gem_codes_to_check(gem_code, downgrade_gems):
    gem_codes_to_check = [gem_code]
    if downgrade_gems == '1':
        gem_data = get_gem_data_by_code(gem_code)
        while True:
            gem_data = get_gem_data_by_type_and_quality(gem_data.type, gem_data.quality + 1)
            if gem_data is None:
                break
            else:
                gem_codes_to_check.append(gem_data.code)
    return gem_codes_to_check


def remove_gem_for_rune_upgrade(item_list, gem_code, downgrade_gems, ignore_gems):
    if gem_code is None or ignore_gems == '1':
        return item_list

    downgrade_needed = False
    gem_removed = False
    for gem_code_to_check in get_gem_codes_to_check(gem_code, downgrade_gems):
        if gem_removed:
            break
        for item in item_list:
            if item.code == gem_code_to_check:
                if downgrade_needed:
                    item_list = downgrade_gem_to(item_list, gem_code_to_check, gem_code)
                    del item_list[-1]
                else:
                    item_list.remove(item)
                gem_removed = True
                break
        downgrade_needed = True
    return item_list


def to_groups(item_list, config):
    # Sort the items into groups. Each group is sorted internally with some criteria, and different groups will never
    # be on the same stash page.

    item_groups = {}
    if "ITEM_GROUP_MISC" not in config:
        config["ITEM_GROUP_MISC"] = {}
    for section in config:
        if section.startswith('ITEM_GROUP_'):
            item_group = section[11:]
            if 'SubGroupByAttribute' in config[section]:
                item_groups[item_group] = {}
            else:
                item_groups[item_group] = []

    for item in item_list:
        added = False

        for group in item_groups:
            add_by_type = "ItemType" not in config["ITEM_GROUP_" + group]
            add_by_quality = "ItemQuality" not in config["ITEM_GROUP_" + group]
            add_by_attribute = "Attribute" not in config["ITEM_GROUP_" + group]

            if "ItemType" in config["ITEM_GROUP_" + group]:
                add_by_type = False
                types = [x.strip() for x in config["ITEM_GROUP_" + group]["ItemType"].split(',')]
                for t in types:
                    if ItemType[t] == item.type:
                        add_by_type = True
                        break

            if "ItemQuality" in config["ITEM_GROUP_" + group]:
                add_by_quality = False
                qualities = [x.strip() for x in config["ITEM_GROUP_" + group]["ItemQuality"].split(',')]
                for q in qualities:
                    if ItemQuality[q] == item.quality:
                        add_by_quality = True
                        break

            if "Attribute" in config["ITEM_GROUP_" + group]:
                add_by_attribute = False
                attributes = [x.strip() for x in config["ITEM_GROUP_" + group]["Attribute"].split(',')]
                for a in attributes:
                    check_against = 1
                    if a[0] == "!":
                        check_against = 0
                        a = a[1:]
                    if getattr(item, a) == check_against:
                        add_by_attribute = True
                        break

            if add_by_type and add_by_quality and add_by_attribute:
                if "SubGroupByAttribute" in config["ITEM_GROUP_" + group]:
                    add_to_group(item_groups[group], item, getattr(item, config["ITEM_GROUP_" + group]["SubGroupByAttribute"]))
                else:
                    add_to_group(item_groups[group], item)
                added = True
                break

        if not added:
            add_to_group(item_groups["MISC"], item)

    for group in item_groups:
        sort_by = []
        if "SortByAttribute" in config["ITEM_GROUP_" + group]:
            sort_by = [x.strip() for x in config["ITEM_GROUP_" + group]["SortByAttribute"].split(',')]
        if 'SubGroupByAttribute' in config["ITEM_GROUP_" + group]:
            for sub_group in sorted(item_groups[group], key=lambda x: [getattr(x, attr, "code") for attr in sort_by]):
                item_groups[group][sub_group].sort(key=lambda x: [getattr(x, attr, "code") for attr in sort_by])
        else:
            item_groups[group].sort(key=lambda x: [getattr(x, attr, "code") for attr in sort_by])

    # Finally, add all sorted groups to the groups list. The ordering here is what will determine the actual order in
    # the stash, so modify to your taste.
    groups = []
    for key in item_groups:
        if isinstance(item_groups[key], dict):
            append_supergroup(groups, item_groups[key])
        else:
            groups.append(item_groups[key])

    # Finally, remove any empty groups to avoid having empty stash pages
    groups = [group for group in groups if group]

    return groups


def to_pages(groups):
    # Take the ordered item groups and put them into virtual stash pages
    pages = []  # List of stash pages
    for group in groups:
        current_page = Page()  # For each group, create a new stash page
        for item in group:  # Then for each item, attempt to insert it somewhere in the page
            if item.num_filled_sockets > 0:
                print(item.to_json())
            if not current_page.insert_item(item):  # If insertion fails, add current page to list of "ready" stash
                # pages, create a new page, and insert item into the new page
                pages.append(current_page)
                current_page = Page()
                current_page.insert_item(item)
        pages.append(current_page)  # When done, add current page to list of "ready" stash
    return pages


def make_stash(path, header, ver, gold, new_pages, ignored_pages):
    # Rewrite the stash file using the new (and ignored) stash pages
    with open(path, "wb") as f:
        # First write header and version
        f.write(header)
        f.write(ver)
        # If the stash is shared ("SSS\0") and ver 2, write the shared gold
        if header == b'SSS\x00' and ver == b'02':
            f.write(gold)
        # If the stash is personal, write 4 junk bytes.
        if header == b'CSTM':
            f.write(b'\x00\x00\x00\x00')

        # Write number of pages. It is possible to write these directly but easier to utilize the existing write_bits
        # method by feeding it some 4-byte string and having it rewrite it, since it already handles the endian issues
        f.write(write_bits(b'\x00\x00\x00\x00', 0, 32, len(ignored_pages) + len(new_pages)))

        # Write each ignored page back into the stash, unmodified from its original form
        for page in ignored_pages:
            f.write(page)

        # For the new pages, first write the header and flags, then the number of items,
        # and then each individual item.
        for page in new_pages:
            if header == b'SSS\x00':  # For shared stashes, turn on the shared stash page flag
                f.write(b'ST\x01\x00\x00\x00\x00JM')
            if header == b'CSTM':  # For personal stashes, keep all flags turned off
                f.write(b'ST\x00\x00\x00\x00\x00JM')
            # IF USING OLDER VERSIONS OF PLUGY, COMMENT OR DELETE THE 4 LINES ABOVE AND UNCOMMENT THE LINE BELOW
            # f.write(b'ST\x00JM')
            f.write(write_bits(b'\x00\x00', 0, 16, page.num_items()))
            for item in page.items:
                f.write(item.data)


def backup_stash(stash_file_path, config):
    # Backup old stash file if indicated in settings
    if config["GENERAL"]["BackupStashFile"] == '1':
        new_path = stash_file_path.rsplit(".", 1)[0] + "_OLD." + stash_file_path.rsplit(".", 1)[1]
        copy(stash_file_path, new_path)


def main():
    # Read config
    config = configparser.ConfigParser()
    config.read("settings.ini")

    # Get stash file from user
    stash_file_path = filedialog.askopenfilename(title="Select shared stash file",
                                                 filetypes=[("PlugY shared stash file", "*.sss"),
                                                            ("PlugY personal stash file", "*.d2x")])

    # Backup old file
    backup_stash(stash_file_path, config)

    # Read stash file and parse items
    header, ver, gold, num_pages, stash_data = read_stash_file(stash_file_path)
    pages_to_ignore, item_list = parse_stash_data(stash_data, config)

    # Upgrade runes
    if (config["UPGRADE_RUNES"]["Enabled"]) == '1':
        runes_to_upgrade = [x.strip() for x in config["UPGRADE_RUNES"]['UpgradeOnly'].split(',')]
        item_list = upgrade_runes(item_list, runes_to_upgrade, config["UPGRADE_RUNES"]["KeepAtLeast"], config["UPGRADE_RUNES"]["DowngradeGems"], config["UPGRADE_RUNES"]["IgnoreGems"])

    # Upgrade gems
    if (config["UPGRADE_GEMS"]["Enabled"]) == '1':
        qualities_to_cube = [GemQuality[x.strip()] for x in config["UPGRADE_GEMS"]['UpgradeOnly'].split(',')]
        item_list = upgrade_gems(item_list, qualities_to_cube, config["UPGRADE_GEMS"]['KeepAtLeast'])

    # Sort items into different groups, and sort each group
    groups = to_groups(item_list, config)

    # Create new stash pages and fill them with the sorted items from the groups
    pages = to_pages(groups)

    # Finally, write all data to a new stash file
    make_stash(stash_file_path, header, ver, gold, pages, pages_to_ignore)


if __name__ == "__main__":
    main()
