from fastapi import FastAPI, WebSocket
from ncellapp import ncell, register


class MyException(Exception):

    def __init__(self, msg) -> None:
        super().__init__(msg)


# Create application
app = FastAPI(title='NcellApp FastAPI')


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('Accepting client connection...')
    await websocket.accept()
    while True:
        try:

            def recieve_text():
                text = websocket.receive_text()
                if text == "exit":
                    raise MyException('Connection exit')
                else:
                    return text

            def register_number(number: str):
                global reg
                reg = register(number)
                otps = reg.sendOtp()
                return int(otps.opStatus)

            await websocket.send_text("Please send your 10 digits phone number as paylod and wait for response. Send exit anytime to quit.")
            number = await recieve_text()
            reg_num = register_number(number)
            if reg_num == 12:
                await websocket.send_text("Please send your OTP as paylod to login.")
                otp = await recieve_text()
                tk = reg.getToken(otp=otp)
                if tk.opStatus == '0':
                    token = tk.content['token']
                    account = ncell(token=token)
                    account.login()

                    async def send_sms(free=False):
                        await websocket.send_text('Send the reciever phone')
                        number = int(await recieve_text())
                        await websocket.send_text('Send your message')
                        msg = await recieve_text()
                        try:
                            if free:
                                account.sendFreeSms(number, msg)
                            else:
                                account.sendSms(number, msg)
                            await websocket.send_text('Sent Message Successfully')
                        except:
                            raise MyException('Invalid Response')

                    async def after_login():
                        print('After Login')
                        possible_paylods = ['view_balance',
                                            'send_sms', 'send_free_sms', 'recharge', 'exit']
                        await websocket.send_json({'possible_paylods': possible_paylods})
                        text = await recieve_text()
                        if text not in possible_paylods:
                            raise MyException(
                                'Please send a valid response. Start OVER!')
                        elif text == "view_balance":
                            balance = account.viewBalance()
                            await websocket.send_json(balance.content)
                            await after_login()
                        elif text == "send_sms":
                            await send_sms()
                        elif text == "send_free_sms":
                            await send_sms(free=True)
                            await after_login()
                        elif text == "recharge":
                            await websocket.send_text("Please send the 16 digit pin.")
                            pin = await recieve_text()
                            account.selfRecharge(pin)
                            await websocket.send_text("Successful")
                            await after_login()

                    print('Before Login')
                    await after_login()

                else:
                    raise MyException('Wrong Token. Start Over!!!')

            else:
                raise MyException('Please Enter a Valid Number')

        except Exception as e:
            print('error: ', e)
            await websocket.send_text(str(e))
            break
    print('Bye..')
