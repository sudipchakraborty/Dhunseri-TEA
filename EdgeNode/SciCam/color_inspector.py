import cv2


class ColorInspector:

    @staticmethod
    def inspect(image, x, y):

        if image is None:
            return

        h, w = image.shape[:2]

        if x < 0 or y < 0 or x >= w or y >= h:
            return

        b, g, r = image[y, x]

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h1, s1, v1 = hsv[y, x]

        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l1, a1, b1 = lab[y, x]

        print("---------------------------------------")
        print(f"Pixel : ({x},{y})")
        print(f"BGR   : ({b},{g},{r})")
        print(f"HSV   : ({h1},{s1},{v1})")
        print(f"LAB   : ({l1},{a1},{b1})")