# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'digikalaextractor.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import re
import requests
from bs4 import BeautifulSoup

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.username = QtWidgets.QLineEdit(self.centralwidget)
        self.username.setGeometry(QtCore.QRect(40, 140, 161, 31))
        self.username.setObjectName("username")
        self.password = QtWidgets.QLineEdit(self.centralwidget)
        self.password.setGeometry(QtCore.QRect(40, 180, 161, 31))
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.run = QtWidgets.QPushButton(self.centralwidget)
        self.run.setGeometry(QtCore.QRect(70, 230, 88, 27))
        self.run.setObjectName("run")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(220, 0, 581, 451))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.output_general = QtWidgets.QTextBrowser(self.tab)
        self.output_general.setGeometry(QtCore.QRect(0, 0, 571, 411))
        self.output_general.setObjectName("output_general")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.log = QtWidgets.QTextBrowser(self.centralwidget)
        self.log.setGeometry(QtCore.QRect(0, 460, 791, 192))
        self.log.setObjectName("log")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 24))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.run.clicked.connect(self.get_data)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def get_data(self):
        self.log.append('starting')
        app.processEvents()
        def dkprice_to_numbers(dkprice):
            '''gets something like ۱۱۷،۰۰۰ تومان and returns 117000'''
            convert_dict = {u'۱': '1', u'۲': '2', u'۳': '3', u'۴': '4', u'۵': '5',
                            u'۶': '6', u'۷': '7', u'۸': '8', u'۹': '9', u'۰': '0', }
            price = u'۰' + dkprice
            for k in convert_dict.keys():
                price = re.sub(k, convert_dict[k], price)

            price = re.sub('[^0-9]', '', price)
            return int(price)


        def extract_data(one_page, all_orders):            
            soup = BeautifulSoup(one_page.text, 'html.parser')
            # there might be more than one table
            for this_table in soup.find_all('div', class_='c-table-order__body'):
                for this_item in this_table.find_all('div', class_='c-table-order__row'):
                    name = this_item.find('span').get_text()
                    dknum = this_item.find(
                        'div', class_='c-table-order__cell--value').get_text()
                    num = dkprice_to_numbers(dknum)
                    dkprice = this_item.find(
                        'div', class_='c-table-order__cell--price-value').get_text()
                    price = dkprice_to_numbers(dkprice)
                    date = soup.find('h4').span.get_text()
                    date = re.sub(u'ثبت شده در تاریخ ', '', date)
                    all_orders.append((date, name, num, price))


        url = 'https://www.digikala.com/users/login/'
        payload = {'login[email_phone]': self.username.text(),
                   'login[password]': self.password.text(), 'remember': 1}
        session = requests.session()
        r = session.post(url, data=payload)
        if r.status_code != 200: #TODO check if login is correct
            self.log.append('Can not login. Status code is %s, exiting' % r.status_code)
        app.processEvents()
        page_number = 1
        orders = session.get(
            'https://www.digikala.com/profile/orders/?page=%i' % page_number)
        soup = BeautifulSoup(orders.text, 'html.parser')

        all_orders = []  # (list of (date, name, number, item_price))

        while not soup.find('div', class_='c-profile-empty'):
            app.processEvents()
            for this_order in soup.find_all('a', class_='btn-order-more'):
                this_order_link = this_order.get('href')
                print('going to fetch: http://digikala.com'+this_order_link)
                one_page = session.get('http://digikala.com'+this_order_link)
                extract_data(one_page, all_orders)
            page_number += 1
            orders = session.get(
                'https://www.digikala.com/profile/orders/?page=%i' % page_number)
            soup = BeautifulSoup(orders.text, 'html.parser')
            self.log.append('going for page number %i' % page_number)

        self.log.append('done')


        total_price = 0
        total_purchase = 0
        for date, name, num, price in all_orders:
            print(date)
            print(name)
            print(num)
            print(price)
            print('------------')
            total_price += price * num
            total_purchase += 1
        self.output_general.setText("کل خرید از دیجیکالا: %s\nتعداد خرید: %s" % (total_price, total_purchase))



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "سابقه من در دیجی کالا"))
        self.username.setText(_translate("MainWindow", ""))
        self.run.setText(_translate("MainWindow", "اجرا"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "اطلاعات عمومی"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "نمودار خرید"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

