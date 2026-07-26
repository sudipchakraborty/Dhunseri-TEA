import cv2

from SciCam.processing.white_balance import WhiteBalanceProcessor

processor = WhiteBalanceProcessor()

cap = cv2.VideoCapture(0)

while True:

    ok, frame = cap.read()

    if not ok:
        break

    balanced = processor.process(frame)

    cv2.imshow("Original", frame)
    cv2.imshow("White Balance", balanced)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()