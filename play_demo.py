import cv2
import os

def play():
    path = "demo_assets/fallback_demo.mp4"
    if not os.path.exists(path):
        print("No fallback found. Run record_demo.py first.")
        return
        
    cap = cv2.VideoCapture(path)
    
    cv2.namedWindow("Demo", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Demo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        cv2.imshow("Demo", frame)
        if cv2.waitKey(33) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    play()
