
# Inf2-IADS Coursework 1, October 2019, reworked October 2021
# Python source file: search_queries.py
# Author: John Longley

# PART C: PROCESSING SEARCH QUERIES
# (template file)


import index_build

index_build.generateMetaIndex('index.txt')

# We find hits for queries using the index entries for the search terms.
# Since index entries for common words may be large, we don't want to
# process the entire index entry before commencing a search.
# Instead, we process the index entry as a stream of items, each of which
# references an occurrence of the search term.

# For example, the (short) index entry

#    'ABC01,23,DEF004,056,789\n'

# generates a stream that successively yields the items

#    ('ABC',1), ('ABC',23), ('DEF',4), ('DEF',56), ('DEF',789), None, None, ...

# Item streams also support peeking at the next item without advancing.

class ItemStream:
    def __init__(self,entryString):
        self.entryString = entryString
        self.pos = 0
        self.doc = 0
        self.comma = 0
    def updateDoc(self):
        if self.entryString[self.pos].isalpha():
            self.doc = self.entryString[self.pos:self.pos+3]
            self.pos += 3
    def peek(self):
        if self.pos < len(self.entryString):
            self.updateDoc()
            self.comma = self.entryString.find(',',self.pos)
                    # yields -1 if no more commas after pos
            line = int(self.entryString[self.pos:self.comma])
                    # magically works even when comma == -1, thanks to \n
            return (self.doc,line)
        # else will return None
    def pop(self):
        e = self.peek()
        if self.comma == -1:
            self.pos = len(self.entryString)
        else:
            self.pos = self.comma + 1
        return e

# Comparing items (treating None as infinity):

def itemBefore(d,e):
    if d is None: return False
    else: return (e is None or d < e)
    # :note that d < e is equivalent to
    # d[0] < e[0] or (d[0]==e[0] and d[1] < e[1]))

# Hit streams (inefficient version):

class HitStream:
    
    def __init__(self,itemStreams,lineWindow):
        self.itemStreams = itemStreams
        self.lineWindow = lineWindow
        # begin by locating the earliest item in any stream:
        self.prev = self.nextItem()
        # store latest hit returned, so we can suppress duplicates:
        self.latestHit = None
        
    def nextItem(self):
        # look for earliest item among heads of item streams:
        i = 0 # :index of earliest item found so far
        j = 1 # :index of currently inspected item
        while j < len(self.itemStreams):
            if itemBefore (self.itemStreams[j].peek(),
                           self.itemStreams[i].peek()):
                i = j # :new earliest item found
            j += 1
        return (self.itemStreams[i].pop(), i)
        # :first component will be None if all streams are used up
        
    def isHit(self,curr,prev): # :do curr and prev together form a hit?
        return (# search terms must be different:
                curr[1] != prev[1] and
                # item and prevItem must be from same book:
                curr[0][0] == prev[0][0] and
                # line numbers must be close enough:
                curr[0][1] - prev[0][1] < self.lineWindow)
    
    def next(self):
        self.curr = self.nextItem()
        # MAIN LOOP: search for next hit
        while (self.curr[0] is not None and
               # avoid returning same result twice:
               (self.prev[0] == self.latestHit or not
                # check if we have a hit:
                self.isHit(self.curr,self.prev))):
            self.prev = self.curr
            self.curr = self.nextItem()
        if self.curr[0] is not None:
            # update and return prev as the hit:
            self.latestHit = self.prev[0]
            self.prev = self.curr
            return self.latestHit
        # else return None

import heapq

# TODO:
# Add your code for HitStreamQ here.

class HitStreamQ:
    
    def __init__(self,itemStreams,lineWindow):
        self.itemStreams = itemStreams
        # :a list of tuples with (index,position of streams in list)
        self.queue = [(s.peek(),self.itemStreams.index(s)) for s in itemStreams]
        # :heapify the list to make it priority queue
        heapq.heapify(self.queue)
        self.lineWindow = lineWindow
        # begin by locating the earliest item in any stream:
        self.prev = self.nextItem()
        # store latest hit returned, so we can suppress duplicates:
        self.latestHit = None
        
    def nextItem(self):
        if (self.queue == []):
            return (None,0) # :first elment is none if all streams are used up
        next = heapq.heappop(self.queue)
        # :pop the item in queue, which by design is the earliest item
        next_i = next[1]
        next_loc = self.itemStreams[next_i].pop() # :pop the itemStream to go to the next one
        if(self.itemStreams[next_i].peek() != None):
            # :push another tuple in from the stream which current earliest item is from
            heapq.heappush(self.queue,(self.itemStreams[next_i].peek(),next_i))
        return (next_loc, next_i)
        
    def isHit(self,curr,prev): # :do curr and prev together form a hit?
        return (# search terms must be different:
                curr[1] != prev[1] and
                # item and prevItem must be from same book:
                curr[0][0] == prev[0][0] and
                # line numbers must be close enough:
                curr[0][1] - prev[0][1] < self.lineWindow)
    
    def next(self):
        self.curr = self.nextItem()
        # MAIN LOOP: search for next hit
        while (self.curr[0] is not None and
               # avoid returning same result twice:
               (self.prev[0] == self.latestHit or not
                # check if we have a hit:
                self.isHit(self.curr,self.prev))):
            self.prev = self.curr
            self.curr = self.nextItem()
        if self.curr[0] is not None:
            # update and return prev as the hit:
            self.latestHit = self.prev[0]
            self.prev = self.curr
            return self.latestHit
        # else return None

# Edit the following line to switch between implementations:
HS = HitStream  # :or HitStreamQ

# Displaying hits as corpus quotations:

import linecache

def displayLines(startref,lineWindow):
    if startref is not None:
        doc = startref[0]
        docfile = index_build.CorpusFiles[doc]
        line = startref[1]
        print ((doc + ' ' + str(line)).ljust(16) +
               linecache.getline(docfile,line).strip())
        for i in range(1,lineWindow):
            print (' '*16 + linecache.getline(docfile,line+i).strip())
        print ('')

def displayHits(hitStream,numberOfHits,lineWindow):
    for i in range(0,numberOfHits):
        startref = hitStream.next()
        if startref is None:
            print('-'*16)
            break
        displayLines(startref,lineWindow)
    linecache.clearcache()
    return hitStream

# Putting it together:

currHitStream = None

currLineWindow = 0

def makeItemStreams(keys):
    indexEntries = [index_build.indexEntryFor(k) for k in keys]
    if not all(indexEntries):
        message = "Words absent from index:  "
        for i in range(0,len(keys)):
            if indexEntries[i] is None:
                message += (keys[i] + " ")
        print(message + '\n')
    return [ItemStream(e) for e in indexEntries if e is not None]
    
def search(keys,lineWindow=1,numberOfHits=5):
    # :deleted minRequired as third parameter
    itemStreams = makeItemStreams(keys)
    if len(itemStreams) >= 2:  # :was minRequired
        global currHitStream, currLineWindow
        currHitStream = HS (itemStreams,lineWindow)
        # :deleted minRequired
        currLineWindow = lineWindow
        displayHits(currHitStream,numberOfHits,lineWindow)

def more(numberOfHits=5):
    global currHitStream, currLineWindow
    displayHits(currHitStream,numberOfHits,currLineWindow)

# For efficiency testing:

def allHits(hitStream):
    hits = []
    curr = hitStream.next()
    while curr is not None:
        hits.append(curr)
        curr = hitStream.next()
    return hits

ordinals = ['first','second','third','fourth','fifth','sixth','seventh',
            'eighth','ninth','tenth','eleventh','twelfth','thirteenth',
            'fourteenth','fifteenth','sixteenth','seventeenth','eighteenth',
            'nineteenth','twentieth','thirtieth','fiftieth','hundredth',
            'thousandth','millionth']

# Example:
# allHits(HitStream(makeItemStreams(ordinals),1))

# End of file
