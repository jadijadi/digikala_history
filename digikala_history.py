# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'digikalaextractor.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
import re
import requests
from bs4 import BeautifulSoup

class ProcessThread(QThread):
    def __init__(self, UI):
        QThread.__init__(self)
        self.UI = UI

    def __del__(self):
        self.wait()

    def run(self):
        if self.UI.username.text() == '':
            self.UI.log.append('لطفا ایمیل خود را وارد کنید')
            return
        if self.UI.password.text() == '':
            self.UI.log.append('لطفا پسورد خود را وارد کنید')
            return

        self.UI.log.append('شروع')
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

        def extract_data(one_page, all_orders, all_post_prices):
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
                    dkdiscount = this_item.find(
                        'div', class_='c-table-order__cell c-table-order__cell--discount').get_text()
                    discount = dkprice_to_numbers(dkdiscount)
                    date = soup.find('h4').span.get_text()
                    date = re.sub(u'ثبت شده در تاریخ ', '', date)
                    all_orders.append((date, name, num, price, discount))

            dkpost_price = soup.find_all('div', class_='c-table-draught__col')[3].get_text()
            post_price = dkprice_to_numbers(dkpost_price)
            all_post_prices.append(post_price)

        self.UI.log.append('تلاش برای ورود')
        url = 'https://www.digikala.com/users/login/'
        payload = {'login[email_phone]': self.UI.username.text(),
                   'login[password]': self.UI.password.text(), 'remember': 1}
        session = requests.session()
        r = session.post(url, data=payload)
        if r.status_code != 200:
            self.UI.log.append('مشکل در اتصال. کد خطا: %s' % r.status_code)
            return False

        successful_login_text = 'سفارش‌های من'
        if re.search(successful_login_text, r.text):
            self.UI.log.append('لاگین موفق')
        else:
            self.UI.log.append('کلمه عبور یا نام کاربری اشتباه است')
            return False

        app.processEvents()
        page_number = 1
        orders = session.get(
            'https://www.digikala.com/profile/orders/?page=%i' % page_number)
        soup = BeautifulSoup(orders.text, 'html.parser')

        all_orders = []  # (list of (date, name, number, item_price))
        all_post_prices = []  # list of post prices

        while not soup.find('div', class_='c-profile-empty'):
            app.processEvents()
            for this_order in soup.find_all('a', class_='btn-order-more'):
                this_order_link = this_order.get('href')
                print('going to fetch: http://digikala.com' + this_order_link)
                one_page = session.get('http://digikala.com' + this_order_link)
                extract_data(one_page, all_orders, all_post_prices)
            self.UI.log.append('بررسی صفحه %i' % page_number)
            page_number += 1
            orders = session.get(
                'https://www.digikala.com/profile/orders/?page=%i' % page_number)
            soup = BeautifulSoup(orders.text, 'html.parser')

        self.UI.log.append('پایان')

        total_price = 0
        total_purchase = 0
        full_purchase_list = ''
        n = 0
        total_post_price = 0
        total_discount = 0
        self.UI.output_general.setRowCount(len(all_orders))

        for date, name, num, price, discount in all_orders:
            this_purchase_str = "تاریخ %s:‌ %s عدد %s, به قیمت هر واحد %s\n" % (
                date, num, name, price)
            full_purchase_list = this_purchase_str + full_purchase_list
            this_product_total_price = (price * num) - discount
            total_price += this_product_total_price
            total_purchase += 1
            total_discount += discount

            self.UI.output_general.setItem(n, 0, QTableWidgetItem(str(date)))
            self.UI.output_general.setItem(n, 1, QTableWidgetItem(str(num)))
            self.UI.output_general.setItem(n, 2, QTableWidgetItem(str(this_product_total_price)))
            self.UI.output_general.setItem(n, 3, QTableWidgetItem(str(discount)))
            self.UI.output_general.setItem(n, 4, QTableWidgetItem(str(name)))
            n = n + 1
        purchase_count = len(all_post_prices)
        for post_price in all_post_prices:
            total_post_price += post_price

        self.UI.output_result.clear()
        price_item = ['کل خرید شما از دیجی کالا:    {} تومان'.format(total_price)]
        total_post_price_item = ['مجموع هزینه ی پست:          {} تومان'.format(total_post_price)]
        total_discount_item = ['مجموع تخفیفات دریافتی:     {} تومان'.format(total_discount)]
        purchase_item = ['تعداد خرید:    {} قطعه'.format(total_purchase)]
        purchase_count_item = ['دفعات خرید:    {} بار'.format(purchase_count)]

        self.UI.output_result.addItems(price_item)
        self.UI.output_result.addItems(total_post_price_item)
        self.UI.output_result.addItems(total_discount_item)
        self.UI.output_result.addItems(purchase_item)
        self.UI.output_result.addItems(purchase_count_item)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(851, 651)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.username = QtWidgets.QLineEdit(self.centralwidget)
        self.username.setGeometry(QtCore.QRect(20, 230, 171, 31))
        self.username.setText("")
        self.username.setObjectName("username")
        self.password = QtWidgets.QLineEdit(self.centralwidget)
        self.password.setGeometry(QtCore.QRect(20, 270, 171, 31))
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.run = QtWidgets.QPushButton(self.centralwidget)
        self.run.setGeometry(QtCore.QRect(60, 320, 88, 27))
        self.run.setObjectName("run")
        self.username.returnPressed.connect(self.run.click)
        self.password.returnPressed.connect(self.run.click)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(210, 10, 625, 511))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.output_general = QtWidgets.QTableWidget(self.tab)
        self.output_general.setGeometry(QtCore.QRect(10, 10, 601, 371))
        self.output_general.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.output_general.setLineWidth(1)
        self.output_general.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.output_general.setShowGrid(True)
        self.output_general.setObjectName("output_general")
        self.output_general.setColumnCount(5)
        self.output_general.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.output_general.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.output_general.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.output_general.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.output_general.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.output_general.setHorizontalHeaderItem(4, item)
        self.output_general.horizontalHeader().setCascadingSectionResizes(False)
        self.output_general.horizontalHeader().setDefaultSectionSize(80)
        self.output_general.horizontalHeader().setMinimumSectionSize(38)
        self.output_general.horizontalHeader().setSortIndicatorShown(False)
        self.output_general.horizontalHeader().setStretchLastSection(True)
        self.output_general.verticalHeader().setCascadingSectionResizes(False)
        self.output_general.verticalHeader().setSortIndicatorShown(False)
        self.output_general.verticalHeader().setStretchLastSection(False)
        self.output_result = QtWidgets.QListWidget(self.tab)
        self.output_result.setGeometry(QtCore.QRect(10, 370, 601, 101))
        self.output_result.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.output_result.setObjectName("output_result")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.log = QtWidgets.QTextBrowser(self.centralwidget)
        self.log.setGeometry(QtCore.QRect(210, 530, 625, 91))
        self.log.setObjectName("log")
        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.pixmap = QPixmap('./logo.png')
        self.logo.setScaledContents(True)
        self.logo.setPixmap(self.pixmap)
        self.logo.setGeometry(QtCore.QRect(20, 30, 171, 171))
        self.logo.setText("")
        self.logo.setObjectName("logo")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 851, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.descriptionbox = QtWidgets.QLabel(self.centralwidget)
        self.descriptionbox.setGeometry(QtCore.QRect(10, 350, 190, 250))
        self.descriptionbox.setWordWrap(True)
        self.descriptionbox.setTextFormat(1)
        self.descriptionbox.setOpenExternalLinks(True)
        self.descriptionbox.setObjectName("descriptionbox")

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)


        self.run.clicked.connect(self.get_data)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def get_data(self):
        self.PT = ProcessThread(self)
        self.PT.start()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "سابقه من در دیجی کالا"))
        self.username.setPlaceholderText(_translate("MainWindow", "Email"))
        self.password.setPlaceholderText(_translate("MainWindow", "Password"))
        self.run.setText(_translate("MainWindow", "اجرا"))
        self.output_general.setSortingEnabled(False)
        item = self.output_general.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "تاریخ"))
        item = self.output_general.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "تعداد"))
        item = self.output_general.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "قیمت کل"))
        item = self.output_general.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "تخفیف"))
        item = self.output_general.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "نام"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "اطلاعات عمومی"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "نمودار خرید"))
        self.descriptionbox.setText("<p>با اجرای برنامه و وارد کردن نام کاربری (ایمیل) و کلمه عبور، برنامه تاریخچه فعالیت شما رو از سایت دیجی کالا دریافت میکنه و نمایش میده.</p><p>اطلاعات شما با هیچ جای دیگری به اشتراک گذاشته نمیشه و هیچ اطلاعات یا کلمه عبوری از شما نگهداری نمیشه.</p><p><i><a href='https://github.com/jadijadi/digikala_history' >سورس برنامه</a></i>")

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    # app.setLayoutDirection(QtCore.Qt.RightToLeft)
    MainWindow = QtWidgets.QMainWindow()
    app_icon = QIcon('./icon.svg')
    MainWindow.setWindowIcon(app_icon)
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
