"""
Supplementary functions and utilities
"""
import random


def random_string():
    """
    Create a random string like 'golden-bear-123' to be used in onboarding channel names
    """
    colors = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Cyan', 'Purple', 'White', 'Black', 'Brown', 'Magenta', 'Tan',
              'Olive', 'Maroon', 'Navy', 'Aquamarine', 'Turquoise', 'Silver', 'Lime', 'Teal', 'Indigo', 'Violet', 'Pink', 'Gray']

    bears = ['black bear', 'brown bear', 'bruin', 'grizzly', 'kermode', 'kermode', 'Kodiak',
             'lip bear', 'panda', 'polar bear', 'sloth', 'sun bear', 'bear', 'bruin', 'ursid']

    return (random.choice(colors) + "-" + random.choice(bears).replace(" ", "-") + "-" + str(random.randint(1000, 9999))).lower()
