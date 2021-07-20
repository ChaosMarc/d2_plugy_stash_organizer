# PlugY Stash Organizer

## What is it?

As the name implies, this is a python script to organize your PlugY v11+ stashes. You can load either a shared (.sss) or personal (.d2x) stash file, and the script will organize the stash. This is a
much more configurable fork of [mrpara's script](https://github.com/mrpara/d2_plugy_stash_organizer).

## How do I use it?

To run this script you need to have [Python](https://www.python.org/downloads/) installed. After that you can simply run the main.py file. A dialog box should pop up and prompt you for the stash file.
Point it to the stash file you want to organize, and click OK. Assuming the script doesn't throw any errors, you're done.

## What settings can I change?

The script's behavior can be altered by editing the Settings.ini file which is divided into multiple sections (e.g. `[GENERAL]`). For most settings 1 means on and 0 means off.

### [GENERAL]

`BackupStashFile = 1`
This will make the script back up your old stash file, appending "OLD" to the end. I do not recommend that you change this.

`IgnoreFirstXPages = 0`
This will ignore the first X pages of the stash. These will not be touched in any way, and the items within them will not be sorted. Useful if you want some specific items on the first pages that
should not be sorted automatically.

### [UPGRADE_GEMS]

`Enabled = 1`
With this setting activated gems will automatically be upgraded to the next quality if you have 3 or more identical gems in your stash.

`KeepAtLeast = 0`
If you want to keep a minimum amount of every gem's quality, increase this number to at least 1. This can be useful for rune upgrades or other cube recipes.

`UpgradeQualitiesOnly = CHIPPED, FLAWED, NORMAL, FLAWLESS`
If you want to exclude certain gem qualities from the automatic upgrade, remove them from this list. For valid values see `item_data.GemQuality`. Perfect gems can't be upgraded and should therefore
not be included.

`UpgradeTypesOnly = GEM_AMETHYST, GEM_DIAMOND, GEM_EMERALD, GEM_RUBY, GEM_SAPPHIRE, GEM_TOPAZ, GEM_SKULL`
If you want to exclude certain gem types from the automatic upgrade, remove them from this list. For valid values see `item_data.gems_types`.

### [UPGRADE_RUNES]

`Enabled = 1`
With this setting activated runes will automatically be upgraded to the next rune (El -> Eld -> Tir -> ...) if you have the appropriate ingredients in your stash.

`KeepAtLeast = 0`
If you want to keep a minimum amount of every rune, increase this number to at least 1.

`UpgradeOnly = r01, r02, r03, r04, r05, r06, r07, r08, r09, r10, r11, r12, r13, r14, r15, r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27, r28, r29, r30, r31, r32`
If you want to exclude certain runes (e.g. Ist (r24) runes) from the automatic upgrade, remove them from this list. For valid values see `item_data.rune_types`. Zod runes (r33) can't be upgraded and
should therefore not be included.

`DowngradeGems = 0`
This option can be considered as a small cheat and is therefore not enabled by default. For rune upgrades above Amn (r10) certain gems are needed. With this setting enabled a gem of a higher quality
is automatically downgraded if the correct gem is not available, but a higher one is. E.g. for upgrading two Mal runes (r23) to an Ist rune (r24) you need a normal amethyst. If you only have a perfect
amethyst, it will be downgraded to three flawless and one of them to three normal ones. After that, one of the normal amethysts will be used to upgrade the runes.

`IgnoreGems = 0`
This option can definitely be considered as a cheat and is therefore not enabled by default. It ignores the need for gems when upgrading runes. E.g. for or upgrading two Mal runes (r23) to an Ist
rune (r24) you don't need to have any gems in your stash.

### [ITEM_GROUP_XYZ]

You can add as many `[ITEM_GROUP_XYZ]` sections as you like with any name after `ITEM_GROUP_` (e.g. `ITEM_GROUP_RUNES`). Each section groups items with certain attributes in your stash. You can select
items for group with a combination of the following settings. All settings are optional but at least one of `ItemType`, `ItemQuality` or `Attribute` has to be present. Each group will be placed in one
or more pages of your stash according to the order of your `[ITEM_GROUP_XYZ]` sections.

`ItemType`
All items in this group must be of the selected item type. Multiple values can be used, e.g. `CHARM_GRAND, CHARM_LARGE, CHARM_SMALL` to collect all charms in one group. For valid values
see `item_data.ItemType`.

`ItemQuality`
All items in this group must be of the selected item quality. Multiple values can be used, e.g. `LOW_QUALITY, NORMAL, HIGH_QUALITY` to collect all non magically (white or grey) in one group. For valid
values see `item_data.ItemQuality`.

`Attribute`
All items in this group must have the selected attribute. Multiple values can be used. Negative checks (items without the attribute) are possible by adding an exclamation mark (!)
in front of the attribute's name. E.g. `has_sockets, !is_runeword` to collect all items with sockets in one group whose socketed items form no runeword. For valid values see all `self.xyz` attributes
in `item.py` which start with `is_xyz` or `has_xyz`.

`SortByAttribute`
Items in a group can be sorted by all `self.xyz` attributes in `item.py`. E.g. `type, quality, level` to sort items in a group first by `item_data.ItemType` (alphabetically), then by
their `item_data.ItemQuality` and finally by their item level.

`SubGroupByAttribute`
If you want to put items in a broader group (e.g. UNIQUE) onto separate pages you can define one (and only one!) `self.xyz` attribute from `item.py` to split them by. E.g. To have all individual
unique items on separated pages use `unique_name`.

`SortSubGroupsByAttribute`
By default, the subgroups are sorted by the attribute defined in `SubGroupByAttribute`. If you group your set items by their set's name (all items of one set are on a the same page)
with `SubGroupByAttribute = set_name`, the groups are sorted alphabetically ("Aldur's Watchtower" comes first). If you want the groups themselves (not the items in the group) sorted differently, you
can overwrite the default sorting with another set of attributes e.g. `set_difficulty, set_name` ("Angelic Raiment" comes first as "Aldur's Watchtower" is a "hell" set).

#### Full example

To group all unique helms together, sort them by their name, put every distinct helm (by name) on a different page and sort each page by the items ethereal state and number of sockets and sort the
groups by the helm's item level, use the following settings

```
[ITEM_GROUP_UNIQUE_HELMS]
ItemQuality = UNIQUE
ItemType = HELM
SortByAttribute = is_ethereal, num_total_sockets
SubGroupByAttribute = unique_name
SortSubGroupByAttribute = level
```

The default settings.ini contains my personal grouping and sorting preferences. Feel free to adjust them to your liking.

## Will it work with older versions of PlugY?

It will most likely *not* work with older versions, as v11.02 introduced some new flags, but it may be possible to make it work. Try commenting out lines 390-393 and uncommenting line 395 in main.py.
If anyone tries this, send me a message, so I know if it works, and I will update accordingly.

## Will it work with [some mod]?

If the mod adds items, then the item data (code, type, size) will need to be added to item_data.py. It will probably work if the mod does not change how the game handles item data, but I offer no
guarantees or support.

## I'm getting a key error while running the script!

Unfortunately it seems like the references I used for item codes are not entirely accurate. If you come across a key error, most likely one of the item codes is wrong. Try googling the item code and
seeing which item it belongs to, and then change the appropriate code in item_data.py. Please let me know if you encounter this, and I will update the repo.

## Future plans

- I'm planning on adding the possibility to group and sort items by magical properties. This includes properties added from combined set items, runewords and socketed items. All properties are being
parsed completely already. Only the grouping and sorting functionality is missing.
- Adding (main) page indices for every group
- Keeping empty pages between groups

If you have some further ideas what could be added, feel free to create an issue for them.
