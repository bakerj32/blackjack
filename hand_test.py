import hand

hand = hand.Hand()
hand.hand = ['AS', 'TH', '3S']

value = hand.compute_value()

print value
