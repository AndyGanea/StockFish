import tkinter as tk
from tkinter import font as tkfont
import cv2
import numpy as np
import random
import time
import datetime
import alpaca_trade_api as tradeapi
import requests

# Initialize Alpaca API for paper trading
APCA_API_KEY_ID = 'PK30U9RUO5TZTQEIVBRV'
APCA_API_SECRET_KEY = '8t5HONsD1VSsHsdGfB2BEgK9iqedGF2K6cbfRyUP'
BASE_URL = 'https://paper-api.alpaca.markets'
alpaca_api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, BASE_URL)


def get_tradable_tickers():
    # Fetch all active assets that are tradable on Alpaca
    assets = alpaca_api.list_assets(status='active')
    tradable_tickers = [asset.symbol for asset in assets if asset.tradable]
    return tradable_tickers

def get_company_name(ticker):
    api_key = 'pTh6XsSEUYWztzotXR8IkCmJMQ2A7YYg'  # Replace 'YOUR_API_KEY' with your actual Financial Modeling Prep API key
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['companyName']
    return "Unknown Company"

def random_stock_selection(tradable_tickers):
    stock1, stock2 = random.sample(tradable_tickers, 2)
    return stock1, stock2

def fish_decision(tank_video_source=0, decision_time_threshold=7):
    cap = cv2.VideoCapture(tank_video_source)
    _, frame = cap.read()
    height, width, _ = frame.shape

    left_timer = 0
    right_timer = 0
    current_side = None
    last_side_change_time = time.time()

    while True:
        _, frame = cap.read()
        frame = cv2.rectangle(frame, (0, 0), (width, height), (255, 255, 255), 5)  # Outline the tank
        frame = cv2.line(frame, (width // 2, 0), (width // 2, height), (255, 255, 255), 3)  # Split line

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 150, 0])
        upper_blue = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            (x, y), radius = cv2.minEnclosingCircle(largest_contour)
            center = (int(x), int(y))
            radius = int(radius)
            cv2.circle(frame, center, radius, (0, 255, 0), 2)  # Draw circle around the fish

            cx = center[0]

            new_side = 'left' if cx < width // 2 else 'right'

            current_time = time.time()
            if current_side is None or new_side != current_side:
                if current_side == 'left':
                    left_timer += current_time - last_side_change_time
                elif current_side == 'right':
                    right_timer += current_time - last_side_change_time
                
                current_side = new_side
                last_side_change_time = current_time
            else:
                if current_side == 'left':
                    left_timer += current_time - last_side_change_time
                elif current_side == 'right':
                    right_timer += current_time - last_side_change_time
                last_side_change_time = current_time

            if left_timer >= decision_time_threshold:
                cap.release()
                cv2.destroyAllWindows()
                return 'left'
            if right_timer >= decision_time_threshold:
                cap.release()
                cv2.destroyAllWindows()
                return 'right'

        cv2.imshow('Fish Tank', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()



def trade(stock):
    print(f"Placing order for {stock}")
    alpaca_api.submit_order(
        symbol=stock,
        qty=1,
        side='buy',
        type='market',
        time_in_force='day'
    )

def create_gui(stock1_name, stock1_full, stock2_name, stock2_full, decision_callback):
    root = tk.Tk()
    root.title("Stock Picker")

    title_font = tkfont.Font(family='Helvetica', size=16, weight="bold")
    content_font = tkfont.Font(family='Helvetica', size=12)

    frame = tk.Frame(root, padx=40, pady=40, bg='black')
    frame.pack(padx=10, pady=10)

    label1 = tk.Label(frame, text=f'{stock1_name}', font=title_font, fg="white", bg="black")
    label1.grid(row=0, column=0, padx=10, pady=10)
    label1_detail = tk.Label(frame, text=f'{stock1_full}', font=content_font, fg="white", bg="black")
    label1_detail.grid(row=1, column=0, padx=10, pady=5)

    label2 = tk.Label(frame, text=f'{stock2_name}', font=title_font, fg="white", bg="black")
    label2.grid(row=0, column=1, padx=10, pady=10)
    label2_detail = tk.Label(frame, text=f'{stock2_full}', font=content_font, fg="white", bg="black")
    label2_detail.grid(row=1, column=1, padx=10, pady=5)

    def open_camera_window():
        winner_stock, winner_full = decision_callback()
        for widget in frame.winfo_children():
            widget.destroy()
        winner_label = tk.Label(frame, text=f"Winner: {winner_stock} {winner_full}", font=title_font, fg="green", bg="black")
        winner_label.pack(pady=20)
        root.after(5000, root.destroy)  # Automatically close after 5 seconds

    root.after(1000, open_camera_window)  # Schedule the camera window to open after 1 second
    root.mainloop()

def fish_stock_picker():
    tradable_tickers = get_tradable_tickers()
    stock1, stock2 = random_stock_selection(tradable_tickers)
    stock1_full = get_company_name(stock1)
    stock2_full = get_company_name(stock2)

    def decision_callback():
        decision = fish_decision()
        chosen_stock = stock1 if decision == 'left' else stock2
        chosen_full = stock1_full if decision == 'left' else stock2_full
        print(f"Fish chose: {chosen_stock}")
        trade(chosen_stock)
        return chosen_stock, chosen_full

    create_gui(stock1, stock1_full, stock2, stock2_full, decision_callback)

if __name__ == "__main__":
    fish_stock_picker()