ll, ur = box["lower-left"], box["upper-right"]          # feet, model coordinates
room   = rectangle(ll.x, ll.y, ur.x, ur.y)
room   = room.difference(union_of_smaller_rooms_on_same_floor)
lon    = lon0 + (x - cx) * 0.3048 / (111320 * cos(lat0))  # feet to degrees
lat    = lat0 + (y - cy) * 0.3048 / 111320
