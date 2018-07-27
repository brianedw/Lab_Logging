class SorterAllocator:
    """
    A class which partitions bounded objects (has a start and stop) by some
    category label and then assigns them a subindex such that no two objects
    occupy the same category:subIndex.  Attempts to do this to minimize the
    maximum subIndex for each category.
    """

    def __init__(self, fCat, fStart, fEnd, items):
        """
        Standard init.  Saves arguments as instance variables.

        Arguments:

        fCat (lambda func -> str) -- extracts category string from item
        fStart (lambda func -> comparable) -- extracts start from item
        fEnd (lambda func -> comparable) -- extracts end from item items
        (list(items)) -- A list of records with start, stop and category
        attributes.
        """

        self.fStart = fStart
        self.fEnd = fEnd
        self.fCat = fCat
        self.items = items
        self.catsHolding = dict()  # dict(mod1=[rec1, rec2], mod2=[rec3,rec4])
        self.slotBanks = dict()

    def partition(self):
        """
        Partitions the items based on category.  Items are stored in a
        dictionary of lists.
        """
        self.catsHolding.clear()
        for item in self.items:
            cat = self.fCat(item)
            if cat in self.catsHolding:
                self.catsHolding[cat].append(item)
            else:
                self.catsHolding[cat] = [item]

    def allocate(self):
        """

        """
        self.slotBanks.clear()
        for (cat, itemsHolding) in self.catsHolding.items():
            slotBank = PlaceAllInAvailableSlots(
                itemsHolding, self.fStart, self.fEnd)
            self.slotBanks[cat] = slotBank


def PlaceInAvailableSlot(slotBank, item, fStart, fEnd):
    """
    Goes through the category slot bank and finds the lowest index slot for
    which appending the item will not cause an overlap with the last item.  If
    there are no available slots, it will create an additional slot in the
    slotbank.

    Arguments:

    slotBank (list(list(item))) -- All placed items in a category.  Each
    sublist (slot) contains nonoverlapping items.
    item (item; LeaseRedord) -- Item to be placed
    fStart (lambda func -> comparable) -- function to obtain start value from
    item
    fEnd (lambda func -> comparable) -- function to obtain end value from item
    """

    availableSlots = []
    for (index, slot) in enumerate(slotBank):
        # There should be no empty slots, as item is placed on slot creation.
        lastItem = slot[-1]
        if fEnd(lastItem) <= fStart(item):
            availableSlots.append((index, fEnd(lastItem)))
    if len(availableSlots) == 0:
        slotBank.append([item])
    else:
        sortKey = lambda slotEnum: slotEnum[0]
        bestSlotEnum = min(availableSlots, key=sortKey)
        slotBank[bestSlotEnum[0]].append(item)


def PlaceAllInAvailableSlots(items, fStart, fEnd):
    """
    Places all the items into the most optimal slots.

    Arguments:
    items (list(LeaseRecord)) -- Items to be placed
    fStart (lambda func -> comparable) -- function to obtain start value from
    item
    fEnd (lambda func -> comparable) -- function to obtain end value from item

    Returns:
        (list(list(item))) -- A populated slotBank for a given category.
    """
    items.sort(key=fStart)
    slotBank = []
    for item in items:
        PlaceInAvailableSlot(slotBank, item, fStart, fEnd)
    return slotBank
