#!/usr/bin/env python
'''
Somewhat contrived example.
'''
from pmf.core import MObject
from pmf.adapters import AllContentNotificationAdapter, NotificationAdapter

class PurchaseOrder(MObject):
    
    '''
    Define containment relationship.
    '''
    mContainment = frozenset(['items'])
    
    def __init__(self):
        MObject.__init__(self)
        self.shipTo = None
        self.billTo = None
        self.items = []
        
class Address(MObject):
    def __init__(self):
        MObject.__init__(self)
        self.name = None
        self.line1 = None
        self.line2 = None
        self.city = None
        self.state = None
        self.zipcode = None
        
class Item(MObject):
    def __init__(self):
        MObject.__init__(self)
        self.upc = None
        self.tags = {}

def po_change(notification):
    '''
    This callback will get called for all change to the purchase order itself
    '''
    print "po_change", notification
    
def all_mo_change(notification):
    '''
    This callback will get called for changes anywhere in
    the PO, included all child elements.
    '''
    print "all_mo_change", notification
    
    # A simple example of using the notification object
    if notification.feature == "PurchaseOrder.shipTo" and \
       notification.eventType == "SET":
        print "New ShipTo", notification.newValue
    if notification.feature == "PurchaseOrder.items" and \
       notification.eventType in ("ADD", "ADD_MANY"):
        print "New Item(s) Added", notification.newValue
    
if __name__ == "__main__":
    # Create a purchase order
    po = PurchaseOrder()
    # Attach an notification listener that will listen to all
    # content of the PurchaseOrder
    po.mAddAdapter(NotificationAdapter(callback=po_change))
    po.mAddAdapter(AllContentNotificationAdapter(callback=all_mo_change))
    
    addr = Address()
    assert addr._mContainer == None
    po.shipTo = addr
    assert addr._mContainer == None # Addresses don't have a contianment relationship
    
    item = Item()
    item.upc = "0123-4567"
    item.tags["condition"] = "good"
    
    assert item._mContainer == None
    po.items.append(item)
    assert item._mContainer == po
    
    # Should trigger an all_mo_change callback
    item.upc = "1111-1111"
    addr.name = "Joe Smith"
