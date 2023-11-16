#!/usr/bin/env python3

# STUDENT version for Project 1.
# TPRG2131 Fall 202x
# Updated Phil J (Fall 202x)
# 
# David Logan
# Oct 20, 2023 - initial version
# Nov 15, 2023 - Updated for Fall 2023.
# 

# PySimpleGUI recipes used:
#
# Persistent GUI example
# https://pysimplegui.readthedocs.io/en/latest/cookbook/#recipe-pattern-2a-persistent-window-multiple-reads-using-an-event-loop
#
# Asynchronous Window With Periodic Update
# https://pysimplegui.readthedocs.io/en/latest/cookbook/#asynchronous-window-with-periodic-update
import PySimpleGUI as sg
from gpiozero import Button, Servo
from time import sleep

hardware_present = False

try:
    from gpiozero import Button, Servo
    button_pin = 5
    servo_pin = 17
    key1 = Button(button_pin)
    servo = Servo(servo_pin)
    # *** define the pin you used
    hardware_present = True
except ModuleNotFoundError:
    print("Not on a Raspberry Pi or gpiozero not installed.")

TESTING = True


def log(s):
    if TESTING:
        print(s)


class VendingMachine(object):
    PRODUCTS = {"Surpise 5¢": 5, "Pop 10¢": 10, "Chips 25¢ ": 25, "Chocolate $1": 100, "Beer $2": 200}

    COINS = {"5¢": 5, "10¢": 10, "25¢": 25, "$1": 100, "$2": 200}

    def __init__(self):
        self.state = None
        self.states = {}
        self.event = ""
        self.amount = 0
        self.change_due = 0
        values = [self.COINS[k] for k in self.COINS]
        self.coin_values = sorted(values, reverse=True)
        log(str(self.coin_values))

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            log('Exiting %s' % (self.state.name))
            self.state.on_exit(self)
        self.state = self.states[state_name]
        log('Entering %s' % (self.state.name))
        self.state.on_entry(self)

    def update(self):
        if self.state:
            self.state.update(self)

    def add_coin(self, coin):
        self.amount += self.COINS[coin]

    def button_action(self):
        self.event = 'RETURN'
        self.update()


class State(object):
    _NAME = ""

    def __init__(self):
        pass

    @property
    def name(self):
        return self._NAME

    def on_entry(self, machine):
        pass

    def on_exit(self, machine):
        pass

    def update(self, machine):
        pass


class WaitingState(State):
    _NAME = "waiting"

    def update(self, machine):
        if machine.event in machine.COINS:
            machine.add_coin(machine.event)
            machine.go_to_state('add_coins')
            window["total_inserted"].update(f'Total Inserted: ${machine.amount / 100:.2f}')




class AddCoinsState(State):
    _NAME = "add_coins"

    def update(self, machine):
        if machine.event == "RETURN":
            machine.go_to_state('count_change')
            window["total_inserted"].update('Total Inserted: $0.00')
        elif machine.event in machine.COINS:
            machine.add_coin(machine.event)
            window["total_inserted"].update(f'Total Inserted: ${machine.amount / 100:.2f}')
        elif machine.event in machine.PRODUCTS:
            if machine.amount >= machine.PRODUCTS[machine.event]:
                machine.go_to_state('deliver_product')
        else:
            pass  # else ignore the event, not enough money for the product


class DeliverProductState(State):
    _NAME = "deliver_product"

    def on_entry(self, machine):
        if machine.amount >= machine.PRODUCTS[machine.event]:
            machine.change_due = machine.amount - machine.PRODUCTS[machine.event]
            machine.amount = 0
            print(f"Dispensing {machine.event}...")
            servo.min()
            sleep(0.5)
            servo.max()
       
        
           
        if machine.change_due > 0:
            machine.go_to_state('count_change')
        else:
            machine.go_to_state('waiting')
        #else:
            #sg.popup_error("Insufficient funds. Please add more coins.")

    def on_exit(self, machine):
        window["total_inserted"].update('Total Inserted: $0.00')
        window["RETURN"].update(disabled=False)


class CountChangeState(State):
    _NAME = "count_change"

    def on_entry(self, machine):
        print("Change due: $%0.2f" % (machine.change_due / 100))
        log("Returning change: " + str(machine.change_due))
        window["total_inserted"].update(f'Total Inserted: ${machine.amount / 100:.2f}')
        window["RETURN"].update(disabled=False)

    def update(self, machine):
        for coin_index in range(0, 5):
            while machine.change_due >= machine.coin_values[coin_index]:
                print("Returning %d" % machine.coin_values[coin_index])
                machine.change_due -= machine.coin_values[coin_index]
        if machine.change_due == 0:
            machine.go_to_state('waiting')


if __name__ == "__main__":
    sg.theme('BluePurple')

    coin_col = []
    coin_col.append([sg.Text("ENTER COINS", font=("Helvetica", 24))])

    for item in VendingMachine.COINS:
        log(item)
        button = sg.Button(item, font=("Helvetica", 18))
        row = [button]
        coin_col.append(row)

    select_col = []
    select_col.append([sg.Text("SELECT ITEM", font=("Helvetica", 24))])
    for item in VendingMachine.PRODUCTS:
        log(item)
        button = sg.Button(item, font=("Helvetica", 18))
        row = [button]
        select_col.append(row)

    layout = [[sg.Column(coin_col, vertical_alignment="TOP"), sg.VSeparator(), sg.Column(select_col, vertical_alignment="TOP")]]
    layout.append([sg.Text("Total Inserted:", font=("Helvetica", 18)), sg.Text("", key="total_inserted", font=("Helvetica", 18))])
    layout.append([sg.Button("RETURN", font=("Helvetica", 12), key="RETURN", disabled=True)])
    window = sg.Window('Vending Machine', layout)


    # Set up the callback
    
    vending = VendingMachine()
    key1.when_pressed = vending.button_action
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    vending.go_to_state('waiting')



    if hardware_present:
        
        # Set up the callback
        key1.when_pressed = vending.button_action

    while True:
        event, values = window.read(timeout=10)
        if event != '__TIMEOUT__':
            log((event, values))
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        vending.event = event
        vending.update()

    window.close()
    print("Normal exit")
