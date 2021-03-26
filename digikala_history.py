# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'digikalaextractor.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

import os
import sys
import qdarkstyle
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, QFile
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.uic import loadUi
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import xlwt

# set the environment variable to use a specific wrapper
# it can be set to pyqt, pyqt5, pyside or pyside2 (not implemented yet)
# you do not need to use QtPy to set this variable
os.environ['QT_API'] = 'pyqt5'

class ProcessThread(QThread):
    def __init__(self, UI):
        QThread.__init__(self)
        self.UI = UI
        
    def __del__(self):
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):
        if self.UI.username.text() == '':
            self.UI.log.append('لطفا ایمیل خود را وارد کنید')
            return
        if self.UI.password.text() == '':
            self.UI.log.append('لطفا پسورد خود را وارد کنید')
            return

        self.UI.log.append('شروع')

        def get_rc_rd(request):
            soup = BeautifulSoup(request.text, 'html.parser')
            inputs = soup.select("form input", {'class': 'c-login__form'})
            return(inputs[0]['value'], inputs[1]['value'])
        
        def get_token(request):
            start, end = request.text.find('token=') + 6, request.text.find('DjxBQ"') + 5
            return request.text[start:end]

        def dkprice_to_numbers(dkprice):
            '''gets something like ۱۱۷،۰۰۰ تومان and returns 117000'''
            convert_dict = {u'۱': '1', u'۲': '2', u'۳': '3', u'۴': '4', u'۵': '5',
                            u'۶': '6', u'۷': '7', u'۸': '8', u'۹': '9', u'۰': '0', }
            price = u'۰' + dkprice
            for k in convert_dict.keys():
                price = re.sub(k, convert_dict[k], price)

            price = re.sub('[^0-9]', '', price)
            return int(price)

        def extract_data(one_page, all_orders, all_post_prices):
            soup = BeautifulSoup(one_page.text, 'html.parser')
            date = soup.find('div', class_='o-box').find('div', class_='c-profile-order__details-top-bar').find('div', class_='c-profile-order__details-header').find('div', class_='c-profile-order__list-item-detail').get_text()

            # there might be more than one table
            for this_table in soup.find_all('div', class_='c-profile-order__list-item-products'):
                for this_item in this_table.find_all('div', class_='c-profile-order__list-item-product'):

                    name = this_item.find('div', class_='c-profile-order__list-item-product-title').get_text()

                    dknum = this_item.find('span', class_='c-profile-order__list-item-parcel-product-qty').get_text()
                    num = dkprice_to_numbers(dknum)

                    dkprices = this_item.find_all('div', class_='c-profile-order__list-item-detail c-profile-order__list-item-detail--currency')
                    price = dkprice_to_numbers(dkprices[0].get_text())

                    dkdiscount = dkprices[1].get_text() if len(dkprices) == 2 else "0" 
                    discount = dkprice_to_numbers(dkdiscount)

                    date2 = re.sub(u'ثبت شده در تاریخ ', '', date)

                    all_orders.append((date2, name, num, price, discount))

            dkpost_price = soup.find('div', class_='o-box').find_all('div', class_='c-profile-order__list-item')
            post_price = 0

            for list_item in dkpost_price:
                temp = list_item.find_all('div', class_='c-profile-order__list-item-detail')
                for item in temp:
                    if item.get_text().find('ارسال') >=0:
                        post_price += dkprice_to_numbers(item.get_text())
                    
            all_post_prices.append(post_price)


        def login(session, email, password):
            url = 'https://www.digikala.com/users/login-register/'
            r = session.get(url)
            rc, rd = get_rc_rd(r)

            payload = {
                'login[email_phone]': email,
                'rc': rc,
                'rd': rd
            }

            url = 'https://www.digikala.com/users/login-register/'
            r = session.post(url, data = payload)
            rc, rd = get_rc_rd(r)

            payload = {
                'login[password]': password,
                'rc': rc,
                'rd': rd
            }
            token = get_token(r)
            type = 'login_by_password'
            _back = 'https://www.digikala.com/profile/'
            url = f'https://www.digikala.com/users/login/confirm/?token={token}&type={type}&_back={_back}'
            r = session.post(url, data = payload)            
            return r

        self.UI.log.append('تلاش برای ورود')

        email =  self.UI.username.text()
        password =  self.UI.password.text()

        session = requests.Session()
        r = login(session, email, password)
        
        if r.status_code != 200:
            self.UI.log.append('مشکل در اتصال. کد خطا: %s' % r.status_code)
            return

        successful_login_text = 'سفارش‌های من'
        failed_login_text = 'اطلاعات کاربری نادرست است'
        
        if r.text.find(successful_login_text) >= 0:
            self.UI.log.append('۱ لاگین موفق')

        elif re.search(failed_login_text, self.UI.username.text()):
            r = login(session, email, password)
            if r.status_code != 200:
                self.UI.log.append('مشکل در اتصال. کد خطا: %s' % r.status_code)
                return
            if r.text.find(successful_login_text) >= 0:
                self.UI.log.append('۲ لاگین موفق')
            elif r.text.find(failed_login_text) >= 0:
                self.UI.log.append('کلمه عبور یا نام کاربری اشتباه است')
                return
            else :
                self.UI.log.append('خطای نا معلوم')
                return
        elif r.text.find(failed_login_text) >= 0:
            self.UI.log.append('کلمه عبور یا نام کاربری اشتباه است')
            print('b')
            return
        else :
            self.UI.log.append('خطای نا معلوم')
            return
        page_number = 1
        orders = session.get(
            'https://www.digikala.com/profile/my-orders/?activeTab=delivered&page=%i' % page_number)
        soup = BeautifulSoup(orders.text, 'html.parser')

        all_orders = []  # (list of (date, name, number, item_price))
        all_post_prices = []  # list of post prices

        while not soup.find('div', class_='c-profile-empty-temporary__img'):
            for mainline in soup.find_all('div', class_='c-profile-order__list-item') :
                for this_order in mainline.find_all('a', class_='o-link o-link--has-arrow') :
                    this_order_link = this_order.get('href')
                    print('going to fetch: http://digikala.com' + this_order_link)
                    one_page = session.get('http://digikala.com' + this_order_link)
                    extract_data(one_page, all_orders, all_post_prices)            
            self.UI.log.append('بررسی صفحه %i' % page_number)
            page_number += 1
            orders = session.get(
                'https://www.digikala.com/profile/my-orders/?activeTab=delivered&page=%i' % page_number)
            soup = BeautifulSoup(orders.text, 'html.parser')


        self.UI.log.append('پایان')

        total_price = 0
        total_purchase = 0
        full_purchase_list = ''
        n = 0
        total_post_price = 0
        total_discount = 0
        self.UI.output_general.setRowCount(len(all_orders))
        self.xData = []
        self.yData = []

        for date, name, num, price, discount in all_orders:
            this_purchase_str = "تاریخ %s:‌ %s عدد %s, به قیمت هر واحد %s\n" % (
                date, num, name, price)
            full_purchase_list = this_purchase_str + full_purchase_list
            this_product_total_price = (price * num) - discount * num
            total_price += this_product_total_price
            total_purchase += 1
            total_discount += discount
            
            self.xData.append(n)
            self.yData.append(this_product_total_price)
            self.UI.output_general.setItem(n, 0, QTableWidgetItem(str(date)))
            self.UI.output_general.setItem(n, 1, QTableWidgetItem(str(num)))
            self.UI.output_general.setItem(
                n, 2, QTableWidgetItem(str(this_product_total_price)))
            self.UI.output_general.setItem(
                n, 3, QTableWidgetItem(str(discount)))
            self.UI.output_general.setItem(n, 4, QTableWidgetItem(str(name)))
            n = n + 1

        self.UI.plot.addData(self.xData, self.yData)
        purchase_count = len(all_post_prices)
        for post_price in all_post_prices:
            total_post_price += post_price

        self.UI.output_result.clear()
        price_item = [
            'کل خرید شما از دیجی کالا:    {} تومان'.format(total_price)]
        total_post_price_item = [
            'مجموع هزینه ی پست:          {} تومان'.format(total_post_price)]
        total_discount_item = [
            'مجموع تخفیفات دریافتی:     {} تومان'.format(total_discount)]
        purchase_item = ['تعداد خرید:    {} قطعه'.format(total_purchase)]
        purchase_count_item = ['دفعات خرید:    {} بار'.format(purchase_count)]

        self.UI.output_result.addItems(price_item)
        self.UI.output_result.addItems(total_post_price_item)
        self.UI.output_result.addItems(total_discount_item)
        self.UI.output_result.addItems(purchase_item)
        self.UI.output_result.addItems(purchase_count_item)
        window.exportCsv.setEnabled(True)
        window.exportExcel.setEnabled(True)
        self.UI.all_orders = all_orders


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def export_csv():
    username = window.username.text()
    now = datetime.now()
    nowStr = now.strftime("%Y-%m-%d--%H-%M-%S")
    fileName = '%s %s.csv' % (username, nowStr)
    with open(fileName, mode='w', encoding='utf-8') as purche_file:
        fieldnames = ["نام", "تخفیف", " قیمت کل", "تعداد", "تاریخ"]
        purche_writer = csv.writer(purche_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        purche_writer.writerow(fieldnames)
        for date, name, num, price, discount in window.all_orders:
            this_product_total_price = (price * num) - discount
            purche_writer.writerow([ name, discount, this_product_total_price, num, date])
    

def export_excel():
    username = window.username.text()
    now = datetime.now()
    nowStr = now.strftime("%Y-%m-%d--%H-%M-%S")
    imgfileName = '%s %s.bmp' % (username, nowStr)
    xlsfilename = '%s %s.xls' % (username, nowStr)
    window.plot.getImage(imgfileName)
    fieldnames = ["سطر","نام", "تخفیف", " قیمت کل", "تعداد", "تاریخ"]
        
    book = xlwt.Workbook(encoding="utf-8")
    sheet = book.add_sheet(username)
    n = 0
    for field in fieldnames:
        sheet.write(0, n, field)
        n = n + 1
    n = 1
    for date, name, num, price, discount in window.all_orders:
        this_product_total_price = (price * num) - discount
        sheet.write(n,0,"%s" % n)
        sheet.write(n,1,"%s" % name)
        sheet.write(n,2,"%s" % discount)
        sheet.write(n,3,"%s" % this_product_total_price)
        sheet.write(n,4,"%s" % num)
        sheet.write(n,5,"%s" % date)
        n = n + 1
    sheet.write(n+2, 1, "نمودار هزینه های انجام شده")
    sheet.insert_bitmap(imgfileName, n+2, 3)
    book.save(xlsfilename)
    os.remove(imgfileName)

def get_data():
    window.PT = ProcessThread(window)
    window.PT.start()
    window.run.setText("توقف")
    window.PT.finished.connect(done)
    window.run.clicked.disconnect(get_data)
    window.run.clicked.connect(window.PT.stop)


def done():
    window.run.setText("اجرا")
    window.run.clicked.disconnect(window.PT.stop)
    window.run.clicked.connect(get_data)


def setupWindow(window):
    # connect signals and slots in here
    window.run.clicked.connect(get_data)
    window.username.returnPressed.connect(window.run.click)
    window.password.returnPressed.connect(window.run.click)
    window.exportCsv.clicked.connect(export_csv)
    window.exportExcel.clicked.connect(export_excel)
    window.exportCsv.setEnabled(False)
    window.exportExcel.setEnabled(False)
    app_icon = QIcon(resource_path("icon.svg"))
    window.setWindowIcon(app_icon)
    app_image = QPixmap("icon.svg")
    window.logo.setMaximumSize(200, 200)
    window.logo.setPixmap(app_image)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    # app.setLayoutDirection(QtCore.Qt.RightToLeft)
    # setup stylesheet
    app.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())

    ui_file = QFile("digikala_history.ui")
    ui_file.open(QFile.ReadOnly)
    window = loadUi(ui_file)
    ui_file.close()
    setupWindow(window)
    window.show()

    sys.exit(app.exec_())
