import sys, random
from PyQt5.uic import loadUi
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QStackedWidget, QMessageBox, QTableWidgetItem, QAction
import mysql.connector as mysql
from pymongo import MongoClient
from datetime import datetime
from dateutil.relativedelta import relativedelta


mySQLpw = "password"
mySQLdb = "oshestest"
mySQLuser = "root"
currUser = ""
cartlist = []
adminlst = []
reqlist = []
servlist = []
customerlst = []
amnt = 0
# mysqlorder= ['customers', 'administrators','products', 'billings','items','requests']

conn = mysql.connect(
    host = "localhost",
    user = mySQLuser,
    password = mySQLpw,
    database = mySQLdb
)
cur = conn.cursor()


cluster = MongoClient('localhost', 27017)
items_collection = cluster["oshes"]["items"]
products_collection = cluster["oshes"]["products"]




class serviceScreen(QDialog):
    def __init__(self):
        super(serviceScreen,self).__init__()
        loadUi("service.ui", self)

        self.tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)

        self.refresh.clicked.connect(lambda: self.servicedisplay())
        self.approve.clicked.connect(lambda: self.approveRequest())
        self.complete.clicked.connect(lambda: self.completeService())
        self.back.clicked.connect(lambda: self.back2adminhome())


    def approveRequest(self):
        indexes = self.tbl.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        print(f"Selected rows: {rows}")

        aList = []
        for row in rows:
            reqIID     = self.tbl.item(row, 4).text()
            servStatus = self.tbl.item(row, 6).text()

            if servStatus == "Waiting for approval":
                aList.append(reqIID)

        conn = mysql.connect(
            host = "localhost",
            user = mySQLuser,
            password = mySQLpw,
            database = mySQLdb
        )
        cur = conn.cursor()

        for IID in aList:
            try:
                sql = "UPDATE requests SET requestStatus = %s, administratorID = %s WHERE itemID = %s"
                val = ["Approved", currUser, IID]
                cur.execute(sql, val)
                sql = "UPDATE items SET servicestatus = %s WHERE itemID = %s"
                val = ["In progress", IID]
                cur.execute(sql, val)
                print("Approved:", IID)

            except:
                print("Failed to approve,", IID)
        conn.commit()
        #self.tbl.setRowCount(0)
        #self.servicedisplay()


    def completeService(self):
        indexes = self.tbl.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        print(f"Selected rows: {rows}")

        aList = []
        for row in rows:
            reqIID     = self.tbl.item(row, 4).text()
            servStatus = self.tbl.item(row, 6).text()

            if servStatus == "In progress":
                aList.append(reqIID)

        conn = mysql.connect(
            host = "localhost",
            user = mySQLuser,
            password = mySQLpw,
            database = mySQLdb
        )
        cur = conn.cursor()

        for IID in aList:
            try:
                sql = "UPDATE requests SET requestStatus = %s WHERE itemID = %s"
                val = ["Completed", IID]
                cur.execute(sql, val)
                sql = "UPDATE items SET servicestatus = %s WHERE itemID = %s"
                val = ["Completed", IID]
                cur.execute(sql, val)
                print("Serviced", IID)

            except:
                print("Failed to service", IID)
        conn.commit()
        #self.tbl.setRowCount(0)
        #self.servicedisplay()


    def servicedisplay(self):
        print("Refreshing...")
        conn = mysql.connect(
            host = "localhost",
            user = mySQLuser,
            password = mySQLpw,
            database = mySQLdb
        )
        cur = conn.cursor()
        sql="SELECT * FROM requests WHERE requestStatus = 'Submitted' OR requestStatus = 'In progress' OR requestStatus = 'Approved'"
        cur.execute(sql)
        records= cur.fetchall()
        conn.commit()

        #               reqStatus    : servStatus
        serviceDict = {"Submitted":"Waiting for approval", "In progress":"Waiting for approval", "Approved":"In progress", "Completed":"Completed"}
        
        row = 0
        for record in records:
            print(record)
            reqID     = str(record[0])
            reqDate   = str(record[1])
            reqStatus = str(record[2])
            reqSfee   = str(record[3])
            reqCID    = str(record[4])
            reqIID    = str(record[5])
            reqAID    = record[6]   # default None (null in mySQL)
            payDate   = record[7]   # default None (null in mySQL)
            payAmnt   = record[8]   # default None (null in mySQL)
            servStatus = serviceDict[reqStatus]
            if not reqAID:
                reqAID = "Unassigned"
            self.tbl.setRowCount(row)
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(reqID))
            self.tbl.setItem(row, 1, QTableWidgetItem(reqDate))
            self.tbl.setItem(row, 2, QTableWidgetItem(reqSfee))
            self.tbl.setItem(row, 3, QTableWidgetItem(reqCID))
            self.tbl.setItem(row, 4, QTableWidgetItem(reqIID))
            self.tbl.setItem(row, 5, QTableWidgetItem(reqAID))
            self.tbl.setItem(row, 6, QTableWidgetItem(servStatus))
            row+=1


    def back2adminhome(self):
        #self.tbl.setRowCount(0)
        widget.setCurrentIndex(4)



class reqCartScreen(QDialog):
    def __init__(self):

        super(reqCartScreen, self).__init__()
        loadUi("reqcart.ui", self)

       
        self.reqtable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.reqtable.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)

        self.submit.clicked.connect(lambda: self.request())
        # self.go2req.clicked.connect(lambda: self.gotoreq())
        self.clearCartBtn.clicked.connect(lambda: self.clearCart())
        self.back2searchBtn.clicked.connect(lambda: self.back2phist())
        self.cancel.clicked.connect(lambda: self.cancelreq())

        


    def cancelreq(self):
        global reqlist

        
        for row in reqlist:
            
            selectedbillingID    = row[0]
            selectedpurchaseDate = row[1]
            selectedcat          = row[2]
            selectedmod          = row[3]
            selectedsfee         = row[4]
            rowindex             = row[5]
            # selectedrstatus      = row[6]


            #print(type(selectedsfee))
            conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                password = mySQLpw,
                database = mySQLdb
            )
            cur = conn.cursor()


            sql = 'SELECT itemID FROM items WHERE billingID = %s'
            val = [selectedbillingID]
            cur.execute(sql,val)
            IID = str(cur.fetchall()[0][0])
            
            
            
            try:
                sqlreqstatus = 'SELECT requestStatus FROM requests WHERE itemID = %s'
                valreqstatus = [IID]
                cur.execute(sqlreqstatus, valreqstatus)
            
                reqstatus = str(cur.fetchall()[0][0])

                if reqstatus == "Submitted" or reqstatus == "Submitted and Waiting for payment" or reqstatus == "In progress" or reqstatus == "Approved":
                    purchasehistory.tbl.setItem(rowindex, 5, QTableWidgetItem("Cancelled"))
                    sqlcancel = "UPDATE requests SET requestStatus = 'Cancelled' WHERE itemID = %s"
                    valcancel = [IID]
                    print("Cancelling item: ", IID)
                    cur.execute(sqlcancel, valcancel)
                    conn.commit()
                elif reqStatus == "Cancelled":
                    self.error.setText("Error: Invalid Request Status/Request Status Already Cancelled")
                
            except:
                self.error.setText("Error: Invalid Request Status/Request Status Already Cancelled")
            
           
            
            
        reqlist = []
        self.reqtable.setRowCount(0)


    def request(self):
        global currUser, reqlist

        rdate = QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)

        # Change to all rows by default
        for row in reqlist:
            # Get table value in cell(row, col)
            selectedbillingID    = row[0]
            selectedpurchaseDate = row[1]
            selectedcat          = row[2]
            selectedmod          = row[3]
            selectedsfee         = row[4]
            rowindex             = row[5]
            # selectedrstatus      = row[6]


            #print(type(selectedsfee))
            conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                password = mySQLpw,
                database = mySQLdb
            )
            cur = conn.cursor()


            sql = 'SELECT itemID FROM items WHERE billingID = %s'
            val = [selectedbillingID]
            cur.execute(sql,val)
            IID = str(cur.fetchall()[0][0])
            print("Item ID:", IID)
            #IIDlist = []
            
            print(selectedsfee)



            if selectedsfee == str(0):
                purchasehistory.tbl.setItem(rowindex, 5, QTableWidgetItem("Submitted"))
                reqStatus = "Submitted"
                servicestatus = "Waiting for approval"
                sqlri ="UPDATE items SET servicestatus = %s WHERE itemID = %s"
                valri =[servicestatus, IID]
                cur.execute(sqlri, valri)
            else:
                purchasehistory.tbl.setItem(rowindex, 5, QTableWidgetItem("Submitted and Waiting for payment"))
                reqStatus = "Submitted and Waiting for payment"
                servicestatus = "Waiting for approval"
                # sqlri ="UPDATE items SET servicestatus = %s WHERE itemID = %s"
                # valri =[servicestatus, IID]
                # cur.execute(sqlri, valri)




            try:
                sqlr = "INSERT INTO requests (requestDate, requestStatus, serviceFee, customerID, itemID) VALUES (%s, %s, %s, %s, %s)"
                valr = [rdate, reqStatus, selectedsfee, currUser, IID]
                cur.execute(sqlr, valr)
            except:
                sqlrerr = "UPDATE requests SET requestDate = %s, requestStatus = %s WHERE itemID = %s"
                valrerr = [rdate, reqStatus, IID]
                
                cur.execute(sqlrerr, valrerr)
               
                print("Duplicate")
            

            

            conn.commit()
        reqlist = []
        self.reqtable.setRowCount(0)



    def gotoreq(self):
        widget.setCurrentIndex(10)


    def clearCart(self):
        global reqlist
        reqlist = []
        self.reqtable.setRowCount(0);


    def back2phist(self):
        self.error.setText("")
        widget.setCurrentIndex(7)
        #print(widget.currentIndex())


class PurchaseHistoryScreen(QDialog):
    def __init__(self):

        super(PurchaseHistoryScreen,self).__init__()
        loadUi("purchasehistory.ui", self)
        
        # self.tbl.setHorizontalHeaderLabels(["Billing ID","Purchase Date", "Item ID", "Service Fee", "Request Status"])
        self.tbl.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.tbl.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        # self.displayp.clicked.connect(lambda: self.fillphist())
        self.add2req.clicked.connect(lambda: self.addreq())
        self.checkreq.clicked.connect(lambda: self.goreqcart())
        self.back.clicked.connect(lambda:self.backtosearch())
        self.amount.clicked.connect(lambda: self.displaytotal())
        self.makepayment.clicked.connect(lambda: self.pay())
        
        

    def pay(self):
        global currUser, amnt 
        
        indexes = self.tbl.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                password = mySQLpw,
                database = mySQLdb
            )
        cur = conn.cursor()

        global reqlist
        for row in rows:
            # Get table value in cell(row, col)
            selectedBID = self.tbl.item(row, 0).text()
            selectedPurDate = self.tbl.item(row, 1).text()
            selectedCat = self.tbl.item(row, 2).text()
            selectedMod = self.tbl.item(row, 3).text()
            selectedfee = self.tbl.item(row, 4).text()
            selectedrstatus = self.tbl.item(row, 5).text()

            sqlb = 'SELECT itemID FROM items WHERE billingID = %s'
            valb = [selectedBID]
            cur.execute(sqlb,valb)
            IID = str(cur.fetchall()[0][0])

            if selectedrstatus == "Submitted and Waiting for payment":
                sql = "UPDATE requests SET requestStatus = 'In progress' WHERE customerID = %s AND itemID = %s AND requestStatus = 'Submitted and Waiting for payment'"
                val = [currUser, IID]
                cur.execute(sql,val)

                sqlri ="UPDATE items SET servicestatus = 'Waiting for approval' WHERE itemID = %s"
                valri =[IID]
                cur.execute(sqlri, valri)

                self.tbl.setItem(row, 5, QTableWidgetItem("In progress"))
                self.error.setText("Payment Made Successfully!")
            else:
                self.error.setText("Item(s) with payment not required added!")
                self.error.setStyleSheet("color: red")

        conn.commit()




    def displaytotal(self):
        global reqlist 
        global amnt 
        amnt = 0
        self.addreq()
        
        try:
            amnt = sum([float(item.data()) for item in self.tbl.selectedIndexes() if item.column() == 4])
            self.payment.setPlainText(str(amnt))
        except:
            amnt = 0
            self.payment.setPlainText(str(amnt))



    def checkWarranty(purchaseDate, warrantyDuration):
        warend = datetime.strptime(purchaseDate, "%Y-%m-%d") + relativedelta(months=int(warrantyDuration))
        print("Warranty ends on: ", warend)

        today = QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)
        reqdate = datetime.strptime(today, "%Y-%m-%d")
        print("Requesting on:", reqdate)

        if warend > reqdate:
            print("Warranty in effect")
            return 1
        print("Warranty expired")
        return 0


    def backtosearch(self):
        widget.setCurrentIndex(5)

    
    def addreq(self):
        indexes = self.tbl.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        global reqlist
        for row in rows:
            # Get table value in cell(row, col)
            selectedBID = self.tbl.item(row, 0).text()
            selectedPurDate = self.tbl.item(row, 1).text()
            selectedCat = self.tbl.item(row, 2).text()
            selectedMod = self.tbl.item(row, 3).text()
            selectedfee = self.tbl.item(row, 4).text()
            
            # try:
            #     selectrstatus = self.tbl.item(row, 5).text()
            # except:
            #     selectedrstatus = "N/A"
            #     print("Request Status empty")
                

            try:
                if (selectedBID, selectedPurDate, selectedCat, selectedMod, selectedfee, row) not in reqlist:
                    reqlist.append((selectedBID, selectedPurDate, selectedCat, selectedMod, selectedfee, row))
            except:
                print("reqlist assignment error")


    def goreqcart(self):
        widget.setCurrentIndex(8)
        indexes = self.tbl.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        # global reqlist
        rowindex = 0
        # for i in range(len(reqlist)):
            # billingid = reqlist[i][0]
            # purchasedate = reqlist[i][1]
            # consumerid = reqlist[i][2]
            # sfee = reqlist[i][3]
            # rstatus = self.tble.item()


        for row in rows:
            # Get table value in cell(row, col)
            billingid = self.tbl.item(row, 0).text()
            purchasedate = self.tbl.item(row, 1).text()
            category = self.tbl.item(row, 2).text()
            model = self.tbl.item(row, 3).text()
            sfee = self.tbl.item(row, 4).text()
            # try:
            #     rstatus = self.tbl.item(row, 5).text()
            #     print(rstatus)
            #     print(type(rstatus))
            #     reqcartscreen.reqtable.setItem(rowindex, 5, QTableWidgetItem("HI"))
            # except:
            #     print("request status empty!")

            reqcartscreen.reqtable.setRowCount(rowindex)
            reqcartscreen.reqtable.insertRow(rowindex)
            reqcartscreen.reqtable.setItem(rowindex, 0 ,QTableWidgetItem(billingid))
            reqcartscreen.reqtable.setItem(rowindex, 1, QTableWidgetItem(purchasedate))
            reqcartscreen.reqtable.setItem(rowindex, 2, QTableWidgetItem(category))
            reqcartscreen.reqtable.setItem(rowindex, 3, QTableWidgetItem(model))
            reqcartscreen.reqtable.setItem(rowindex, 4, QTableWidgetItem(sfee))
            try:
                rstatus = self.tbl.item(row, 5).text()
                print(rstatus)
                print(type(rstatus))
                reqcartscreen.reqtable.setItem(rowindex, 5, QTableWidgetItem(rstatus))
            except:
                print("request status empty!")
            

            rowindex+=1

        reqcartscreen.reqtable.resizeColumnsToContents()
        reqcartscreen.reqtable.resizeRowsToContents()


class CartScreen(QDialog):
    def __init__(self):
        super(CartScreen, self).__init__()
        loadUi("cart.ui", self)

        #self.carttable.setHorizontalHeaderLabels(["Category", "Model", "Price ($)", "Warranty (months)", "Color", 
        #                                           "Power Supply", "Factory", "Production Year", "Inventory"])
        self.carttable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.carttable.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)

        self.purchaseBtn.clicked.connect(lambda: self.purchase())
        self.clearCartBtn.clicked.connect(lambda: self.clearCart())
        self.back2searchBtn.clicked.connect(lambda: self.back2search())

    def togglePurchaseStatusList(self, IID_list):
        oldStatus = []
        newStatus = []
        # ItemIDs are strings!
        for IID in IID_list:
            cur = items_collection.find({"ItemID":IID}, {"_id":0, "PurchaseStatus": 1})
            oldStatus.append(cur[0]["PurchaseStatus"])
        print("Toggling PurchaseStatusfor:", IID_list)
        #print(oldStatus)
        for s in oldStatus:
            if s == "Unsold":
                newStatus.append("Sold")
            elif s == "Sold":
                newStatus.append("Unsold")
        #print(newStatus)
        
        for i in range(len(IID_list)):
            items_collection.update_one({"ItemID":IID_list[i]}, {"$set":{"PurchaseStatus":newStatus[i]}})
    
   # TODO (Make it dbl click to edit, or spinbox)
    def purchase(self):
        purchase_list = []

        # Change to all rows by default
        for row in range(self.carttable.rowCount()):
            # Get table value in cell(row, col)
            selectedCat = self.carttable.item(row, 0).text()
            selectedMod = self.carttable.item(row, 1).text()
            selectedPrc = self.carttable.item(row, 2).text()
            selectedWar = self.carttable.item(row, 3).text()
            selectedClr = self.carttable.item(row, 4).text()
            selectedPwr = self.carttable.item(row, 5).text()
            selectedFac = self.carttable.item(row, 6).text()
            selectedPyr = self.carttable.item(row, 7).text()
            selectedInv = int(self.carttable.item(row, 8).text())
            selectedInCart = int(self.carttable.item(row, 9).text())

            if selectedInCart > selectedInv:
                print("Error: Attempting to purchase more than available")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Purchasing Error")
                msg.setText("Insufficient stock in inventory, please reduce item quantity.")
                msg.exec_()
                return

            if (selectedCat, selectedMod, selectedPrc, selectedWar, selectedClr, selectedPwr, selectedFac, selectedPyr, selectedInCart) not in purchase_list:
                purchase_list.append((selectedCat, selectedMod, selectedPrc, selectedWar, selectedClr, selectedPwr, selectedFac, selectedPyr, selectedInCart))

        # Checks complete, beginning purchase
        purchased_IIDs = []
        for i in purchase_list:
            cat = i[0]
            mod = i[1]
            prc = i[2]
            war = i[3]
            clr = i[4]
            pwr = i[5]
            fac = i[6]
            pyr = i[7]
            fltr = {"Category": cat, "Model": mod, "PurchaseStatus": "Unsold",
                    "Color": clr, "PowerSupply": pwr, "Factory": fac, "ProductionYear":pyr}
            purchased_IIDs += items_collection.find(filter = fltr).distinct("ItemID")[0:i[8]]
        print("Purchasing:", purchased_IIDs)

        pdate = QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)
        ptime = QtCore.QTime.currentTime().toString()
        billingid = currUser + pdate.replace("-", "") + ptime.replace(":", "")

        conn = mysql.connect(
            host = "localhost",
            user = "root",
            passwd = mySQLpw,
            database = mySQLdb
        )
        cur = conn.cursor()
        
        n = 0
        for IID in purchased_IIDs:
            # Insert [billingid, pdate, currUser] in mySQL Billings entity
            billing_info = [billingid + str(n), pdate, currUser]
            sql = "INSERT INTO billings VALUES (%s, %s, %s)"
            cur.execute(sql, billing_info)

            # Add billingID to items and toggle purchase status (mySQL)
            billing_info = [billingid + str(n), "Sold", IID]
            sql = "UPDATE items SET billingID = %s, purchasestatus = %s WHERE itemID = %s"
            cur.execute(sql, billing_info)
            n += 1
        conn.commit()

        # Toggle purchase status (mongo)
        self.togglePurchaseStatusList(IID_list = purchased_IIDs)

        # Clear carttable and advsearchtable
        self.clearCart()
        search.advsearchtable.setRowCount(0);

    def clearCart(self):
        global cartlist
        cartlist = []
        self.carttable.setRowCount(0);


    def back2search(self):
        widget.setCurrentIndex(5)
        #print(widget.currentIndex())



class SearchScreen(PurchaseHistoryScreen):
    def __init__(self):
        super(SearchScreen, self).__init__()
        loadUi("advsearch.ui", self)

        self.advsearchBtn.clicked.connect(lambda: self.advsearchFunc())

        self.add2cartBtn.clicked.connect(lambda: self.add2cart())
        self.go2cartBtn.clicked.connect(lambda: self.go2cart())
        self.logoutBtn.clicked.connect(lambda: self.logout())
        self.purchasehist.clicked.connect(lambda: self.request())
        self.purchasehist.clicked.connect(lambda: self.fillphist())



    def add2cart(self):
        indexes = self.advsearchtable.selectionModel().selectedRows()
        rows = [i.row() for i in indexes]
        print(f"Selected rows: {rows}")
        global cartlist
        for row in rows:
            # Get table value in cell(row, col)
            selectedCat = self.advsearchtable.item(row, 0).text()
            selectedMod = self.advsearchtable.item(row, 1).text()
            selectedPrc = self.advsearchtable.item(row, 2).text()
            selectedWar = self.advsearchtable.item(row, 3).text()
            selectedClr = self.advsearchtable.item(row, 4).text()
            selectedPwr = self.advsearchtable.item(row, 5).text()
            selectedFac = self.advsearchtable.item(row, 6).text()
            selectedPyr = self.advsearchtable.item(row, 7).text()
            if (selectedCat, selectedMod, selectedPrc, selectedWar, selectedClr, selectedPwr, selectedFac, selectedPyr) not in cartlist:
                cartlist.append((selectedCat, selectedMod, selectedPrc, selectedWar, selectedClr, selectedPwr, selectedFac, selectedPyr))
        #print("Adding to Cart:")
        #for i in cartlist:
        #   print(i)

    def request(self):
        widget.setCurrentIndex(7)

    def existingreqcheck(self, iid):
        global currUser

        sql = 'SELECT * FROM requests WHERE customerID = %s AND itemID = %s'
        val =[currUser, iid]
        cur.execute(sql,val)
        results = cur.fetchall()

        try:
            for row in results:
                requestStatus = row[2]
            # print(requestStatus)
            return requestStatus
        except:
            return 0

    def fillphist(self):
        global currUser
        
        conn = mysql.connect(
                    host = "localhost",
                    user = mySQLuser,
                    password = mySQLpw,
                    database = mySQLdb
                )
        cur = conn.cursor()

        def checkWarranty(purchaseDate, warrantyDuration):
            warend = datetime.strptime(purchaseDate, "%Y-%m-%d") + relativedelta(months=int(warrantyDuration))
            print("Warranty ends on: ", warend)

            today = QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)
            reqdate = datetime.strptime(today, "%Y-%m-%d")
            print("Requesting on:", reqdate)

            if warend > reqdate:
                print("Warranty in effect")
                return 1
            print("Warranty expired")
            return 0

        # sqlex = SELECT



        query = 'SELECT * FROM billings WHERE customerID =\''+currUser+"\'"
        cur.execute(query)
        custphist = cur.fetchall()

        # print(custphist)
        # print(len(custphist))

        
            
        for row, (billingid, purchasedate, userid) in enumerate(custphist):
            sql = "SELECT itemID FROM items WHERE billingID = %s"
            cur.execute(sql, [billingid])
            records = cur.fetchall()
            itemID = records[0][0]
            purchasehistory.tbl.setRowCount(row)
            purchasehistory.tbl.insertRow(row)
            
            purchasehistory.tbl.setItem(row, 0, QTableWidgetItem(billingid))
            purchasehistory.tbl.setItem(row, 1, QTableWidgetItem(str(purchasedate)))
            


            sql = "SELECT category, model FROM items WHERE itemID = %s"
            cur.execute(sql, [itemID])
            records = cur.fetchall()
            cat = records[0][0]
            mod = records[0][1]

            # print(type(cat))
            purchasehistory.tbl.setItem(row, 2, QTableWidgetItem(cat))
            purchasehistory.tbl.setItem(row, 3, QTableWidgetItem(mod))


            sql = "SELECT `cost ($)`, `warranty (months)` FROM products WHERE category = %s AND model = %s"
            cur.execute(sql, [cat, mod])
            records = cur.fetchall()
            cost = records[0][0]
            war = records[0][1]



            if checkWarranty(str(purchasedate), war):
                print("Set servicefee = 0 in ui table")     
                purchasehistory.tbl.setItem(row, 4, QTableWidgetItem("0"))

            else:
                print("calculate service fee")
                fee = 40 + (0.2*cost)
                purchasehistory.tbl.setItem(row, 4, QTableWidgetItem(str(fee)))

            if self.existingreqcheck(itemID):
                sql = 'SELECT * FROM requests WHERE customerID = %s AND itemID = %s'
                val =[currUser, itemID]
                cur.execute(sql,val)
                results = str(cur.fetchall()[0][2])
                print(results)
                purchasehistory.tbl.setItem(row, 5, QTableWidgetItem(results))


        conn.commit()



    def go2cart(self):
        widget.setCurrentIndex(6)

        rowindex = 0
        for i in range(len(cartlist)):
            cat = cartlist[i][0]
            mod = cartlist[i][1]
            prc = cartlist[i][2]
            war = cartlist[i][3]
            clr = cartlist[i][4]
            pwr = cartlist[i][5]
            fac = cartlist[i][6]
            pyr = cartlist[i][7]
            fltr={"Category": cat, "Model": mod, "PurchaseStatus": "Unsold",
                    "Color": clr, "PowerSupply": pwr, "Factory": fac, "ProductionYear":pyr}

            inv = items_collection.find(filter=fltr).count()
            #comparison in prog, count() getting deprecated
            #print("count_documents:", items_collection.count_documents(filter=fltr))
            #print("count:", inv)
            cart.carttable.setRowCount(rowindex)
            cart.carttable.insertRow(rowindex)
            cart.carttable.setItem(rowindex, 0, QTableWidgetItem(cat))          # "Category"
            cart.carttable.setItem(rowindex, 1, QTableWidgetItem(mod))          # "Model"
            cart.carttable.setItem(rowindex, 2, QTableWidgetItem(str(prc)))     # "Price ($)"
            cart.carttable.setItem(rowindex, 3, QTableWidgetItem(str(war)))     # "Warranty (months)"
            cart.carttable.setItem(rowindex, 4, QTableWidgetItem(clr))          # "Color"
            cart.carttable.setItem(rowindex, 5, QTableWidgetItem(pwr))          # "PowerSupply"
            cart.carttable.setItem(rowindex, 6, QTableWidgetItem(fac))          # "Factory"
            cart.carttable.setItem(rowindex, 7, QTableWidgetItem(str(pyr)))     # "ProductionYear"
            cart.carttable.setItem(rowindex, 8, QTableWidgetItem(str(inv)))     # "Inventory"
            cart.carttable.setItem(rowindex, 9, QTableWidgetItem("1"))          # "In Cart"
            #spin = QSpinBox()
            #cart.carttable.setIndexWidget (rowindex, 9, spin)
            rowindex += 1
        cart.carttable.resizeColumnsToContents()
        cart.carttable.resizeRowsToContents()


    def logout(self):
        global currUser, cartlist
        currUser = ""
        cartlist = []
        widget.setCurrentIndex(0)
        # wipe all fields like self.catsearch.text().strip(" ") or wipe somewhere else?
        login.userfield.setText("")
        login.passwordfield.setText("")


    def advsearchFunc(self):
        cat = self.catsearch.text().strip(" ") # Category
        mod = self.modsearch.text().strip(" ") # Model
        input_clr = [self.clrsearch.text().strip(" ")] # Color
        input_pwr = [self.pwrsearch.text().strip(" ")] # Power Supply
        input_fac = [self.facsearch.text().strip(" ")] # Factory
        input_pyr = [self.pyrsearch.text().strip(" ")] # Production Year

        catModLst = []
        #catModLst = [(Category, Model, Price, Warranty)]
        if (not cat) and (not mod):
            presults = products_collection.find()
        elif not mod:
            presults = products_collection.find({"Category": cat})
        elif not cat:
            presults = products_collection.find({"Model": mod})
        else:
            presults = products_collection.find({"Category": cat, "Model": mod})

        for p in presults:
            catModLst.append((p["Category"], p["Model"], p["Price ($)"], p["Warranty (months)"]))

        ########
        rowindex = 0
        for i in range(len(catModLst)):
            cat = catModLst[i][0]
            mod = catModLst[i][1]
            prc = catModLst[i][2]
            war = catModLst[i][3]

            iresults = items_collection.find({"Category":cat, "Model":mod})

            if input_clr == [""]:
                search_clr = iresults.distinct("Color")
            else:
                search_clr = input_clr

            if input_pwr == [""]:
                search_pwr = iresults.distinct("PowerSupply")
            else:
                search_pwr = input_pwr

            if input_fac == [""]:
                search_fac = iresults.distinct("Factory")
            else:
                search_fac = input_fac

            if input_pyr == [""]:
                search_pyr = iresults.distinct("ProductionYear")
            else:
                search_pyr = input_pyr

            for clr in search_clr:
                for pwr in search_pwr:
                    for fac in search_fac:
                        for pyr in search_pyr:
                            fltr={'Category': cat, 'Model': mod, 'PurchaseStatus': 'Unsold',
                                    "Color": clr, "PowerSupply": pwr, "Factory": fac, "ProductionYear":pyr}
                            inv = items_collection.find(filter=fltr).count()
                            #print(cat, mod, prc, war, clr, pwr, fac, pyr, inv)
                            if inv>0:
                                #print("Filter:", cat, mod, prc, war, clr, pwr, fac, pyr, inv)
                                self.advsearchtable.setRowCount(rowindex)
                                self.advsearchtable.insertRow(rowindex)
                                self.advsearchtable.setItem(rowindex, 0, QTableWidgetItem(cat))         #details["Category"]
                                self.advsearchtable.setItem(rowindex, 1, QTableWidgetItem(mod))         #details["Model"]
                                self.advsearchtable.setItem(rowindex, 2, QTableWidgetItem(str(prc))) #str(details["Price ($)"])
                                self.advsearchtable.setItem(rowindex, 3, QTableWidgetItem(str(war))) #str(details["Warranty (months)"])
                                self.advsearchtable.setItem(rowindex, 4, QTableWidgetItem(clr))         #details["Color"]
                                self.advsearchtable.setItem(rowindex, 5, QTableWidgetItem(pwr))         #details["PowerSupply"]
                                self.advsearchtable.setItem(rowindex, 6, QTableWidgetItem(fac))         #details["Factory"]
                                self.advsearchtable.setItem(rowindex, 7, QTableWidgetItem(str(pyr))) #str(details["ProductionYear"])
                                self.advsearchtable.setItem(rowindex, 8, QTableWidgetItem(str(inv))) #str(details["Inventory"])
                                rowindex += 1
            search_clr = [""]
            search_pwr = [""]
            search_fac = [""]
            search_pyr = [""]

        self.advsearchtable.resizeColumnsToContents()
        self.advsearchtable.resizeRowsToContents()



class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen,self).__init__()
        loadUi("welcomescreen.ui", self)
        self.loginbutton.clicked.connect(lambda: self.gotologin()) 
        self.registerbutton.clicked.connect(lambda: self.gotoregister()) 
        
    def gotologin(self):
        widget.setCurrentIndex(2)
        #login = CustomerLoginScreen()
        #widget.addWidget(login)
        #widget.setCurrentIndex(widget.currentIndex()+1) 

    def gotoregister(self):
        widget.setCurrentIndex(1)
        #register = RegisterScreen()
        #widget.addWidget(register)
        #widget.setCurrentIndex(widget.currentIndex()+1) 



class CustomerLoginScreen(QDialog):
    def __init__(self):
        super(CustomerLoginScreen,self).__init__()
        loadUi("customerlogin.ui", self)

        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.showpassword.clicked.connect(lambda: self.togglepasswordvisibility())

        self.login.clicked.connect(lambda: self.customerloginfunction())
        self.adminlogin.clicked.connect(lambda: self.gotoadminlogin())

        self.back.clicked.connect(lambda: self.gotowelcome())

    def gotowelcome(self):
        widget.setCurrentIndex(0)
        #welcome = WelcomeScreen()
        #widget.addWidget(welcome)
        #widget.setCurrentIndex(widget.currentIndex()+1) 

    def gotoadminlogin(self):
        widget.setCurrentIndex(3)
        #adminlogin = AdminLoginScreen()
        #widget.addWidget(adminlogin)
        #widget.setCurrentIndex(widget.currentIndex()+1) 

    def gotoproductsearch(self):
        widget.setCurrentIndex(5)
        #productsearch = ProductScreen()
        #widget.addWidget(productsearch)
        #widget.setCurrentIndex(widget.currentIndex()+1) 

    def togglepasswordvisibility(self):
        if self.passwordfield.echoMode()==QtWidgets.QLineEdit.Password:
            self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)

    def customerloginfunction(self):
        global currUser
        userID = self.userfield.text()
        password = self.passwordfield.text()

        if len(userID) == 0 or len(password) == 0:
            self.error.setText("Please input all fields.")
            
        else:
            try:
                conn = mysql.connect(
                    host = "localhost",
                    user = mySQLuser,
                    passwd = mySQLpw,
                    database = mySQLdb
                )
            
        
                cur = conn.cursor()
                query = 'SELECT password from customers WHERE customerID =\''+userID+"\'"
                checkuser = cur.execute(query)
                result_pass = cur.fetchone()[0]

                if result_pass== password:
                    currUser = userID
                    self.error.setText("")
                    print("Successfully logged in")
                    self.gotoproductsearch()

                else:
                    self.error.setText("Invalid username or password")
            except:
                self.error.setText("Invalid username or password")
            #for x in result_pass:
                #print(x)
            #print(result_pass)


          
            

class AdminSearchScreen(QDialog):
    def __init__(self):
        super(AdminSearchScreen, self).__init__()
        loadUi("adminsearch.ui", self)

        self.adminsearchBtn.clicked.connect(lambda: self.adminsearchFunc())
        self.back2adminhomeBtn.clicked.connect(lambda: self.back2adminhome())


    def adminsearchFunc(self):
        IID = self.IIDsearch.text().strip(" ") # ItemID (Expect single result)
        if IID:
            # Get Product, Model from items collection
            # Get ProductID, Cost ($), Price ($), Warranty (months) form products collection
            iresults = items_collection.find({"ItemID": IID})[0]
            cat = iresults["Category"]
            mod = iresults["Model"]

            presults = products_collection.find({"Category": cat, "Model": mod})[0]
            PID = presults["ProductID"]
            cst = presults["Cost ($)"]
            prc = presults["Price ($)"]
            war = presults["Warranty (months)"]

            clr = iresults["Color"]
            pwr = iresults["PowerSupply"]
            fac = iresults["Factory"]
            pyr = iresults["ProductionYear"]
            if iresults["PurchaseStatus"] == "Sold":
                inv, sld = "0", "1"
            else:
                inv, sld = "1", "0"
            self.adminsearchtable.setRowCount(0)
            self.adminsearchtable.insertRow(0)
            self.adminsearchtable.setItem(0, 0, QTableWidgetItem(cat))
            self.adminsearchtable.setItem(0, 1, QTableWidgetItem(mod))
            self.adminsearchtable.setItem(0, 2, QTableWidgetItem(str(PID)))
            self.adminsearchtable.setItem(0, 3, QTableWidgetItem(str(cst)))
            self.adminsearchtable.setItem(0, 4, QTableWidgetItem(str(prc)))
            self.adminsearchtable.setItem(0, 5, QTableWidgetItem(str(war)))
            self.adminsearchtable.setItem(0, 6, QTableWidgetItem(clr))
            self.adminsearchtable.setItem(0, 7, QTableWidgetItem(pwr))
            self.adminsearchtable.setItem(0, 8, QTableWidgetItem(fac))
            self.adminsearchtable.setItem(0, 9, QTableWidgetItem(pyr))
            self.adminsearchtable.setItem(0, 10, QTableWidgetItem(inv))
            self.adminsearchtable.setItem(0, 11, QTableWidgetItem(sld))

        else:
            cat = self.catsearch.text().strip(" ") # Category
            mod = self.modsearch.text().strip(" ") # Model
            input_clr = [self.clrsearch.text().strip(" ")] # Color
            input_pwr = [self.pwrsearch.text().strip(" ")] # Power Supply
            input_fac = [self.facsearch.text().strip(" ")] # Factory
            input_pyr = [self.pyrsearch.text().strip(" ")] # Production Year
    
            catModLst = []
            
            if (not cat) and (not mod):
                presults = products_collection.find()
            elif not mod:
                presults = products_collection.find({"Category": cat})
            elif not cat:
                presults = products_collection.find({"Model": mod})
            else:
                presults = products_collection.find({"Category": cat, "Model": mod})
    
            for p in presults:
                catModLst.append((p["Category"], p["Model"], p["ProductID"], p["Cost ($)"], p["Price ($)"], p["Warranty (months)"]))
            
            rowindex = 0
            for i in range(len(catModLst)):
                cat = catModLst[i][0]
                mod = catModLst[i][1]
                PID = catModLst[i][2]
                cst = catModLst[i][3]
                prc = catModLst[i][4]
                war = catModLst[i][5]
                
                iresults = items_collection.find({"Category":cat, "Model":mod})
                
                if input_clr == [""]:
                    search_clr = iresults.distinct("Color")
                else:
                    search_clr = input_clr

                if input_pwr == [""]:
                    search_pwr = iresults.distinct("PowerSupply")
                else:
                    search_pwr = input_pwr

                if input_fac == [""]:
                    search_fac = iresults.distinct("Factory")
                else:
                    search_fac = input_fac

                if input_pyr == [""]:
                    search_pyr = iresults.distinct("ProductionYear")
                else:
                    search_pyr = input_pyr
                    
                for clr in search_clr:
                    for pwr in search_pwr:
                        for fac in search_fac:
                            for pyr in search_pyr:
                                fltr = {"Category": cat, "Model": mod, "Color": clr, "PowerSupply": pwr, "Factory": fac, "ProductionYear":pyr}
                                inv = items_collection.count_documents({**fltr, **{"PurchaseStatus": "Unsold"}})
                                sld = items_collection.count_documents({**fltr, **{"PurchaseStatus": "Sold"}})
                                self.adminsearchtable.setRowCount(rowindex)
                                self.adminsearchtable.insertRow(rowindex)
                                self.adminsearchtable.setItem(rowindex, 0, QTableWidgetItem(cat))
                                self.adminsearchtable.setItem(rowindex, 1, QTableWidgetItem(mod))
                                self.adminsearchtable.setItem(rowindex, 2, QTableWidgetItem(str(PID)))
                                self.adminsearchtable.setItem(rowindex, 3, QTableWidgetItem(str(cst)))
                                self.adminsearchtable.setItem(rowindex, 4, QTableWidgetItem(str(prc)))
                                self.adminsearchtable.setItem(rowindex, 5, QTableWidgetItem(str(war)))
                                self.adminsearchtable.setItem(rowindex, 6, QTableWidgetItem(clr))
                                self.adminsearchtable.setItem(rowindex, 7, QTableWidgetItem(pwr))
                                self.adminsearchtable.setItem(rowindex, 8, QTableWidgetItem(fac))
                                self.adminsearchtable.setItem(rowindex, 9, QTableWidgetItem(pyr))
                                self.adminsearchtable.setItem(rowindex, 10, QTableWidgetItem(str(inv)))
                                self.adminsearchtable.setItem(rowindex, 11, QTableWidgetItem(str(sld)))
                                rowindex += 1
                search_clr = [""]
                search_pwr = [""]
                search_fac = [""]
                search_pyr = [""]


        self.adminsearchtable.resizeColumnsToContents()
        self.adminsearchtable.resizeRowsToContents()


    def back2adminhome(self):
        searchBoxes = [self.catsearch, self.modsearch, self.clrsearch, self.pwrsearch, self.facsearch, self.pyrsearch, self.IIDsearch]
        [i.setText("") for i in searchBoxes]
        widget.setCurrentIndex(4)



class AdminLoginScreen(WelcomeScreen, CustomerLoginScreen):
    def __init__(self):
        super(AdminLoginScreen, self).__init__()
        loadUi("administratorlogin.ui", self)

        
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.showpassword.clicked.connect(lambda: self.togglepasswordvisibility())

        self.login.clicked.connect(lambda: self.adminloginfunction())

        self.back.clicked.connect(lambda: self.gotowelcome())
        

    def gotoadminhome(self):
        widget.setCurrentIndex(4)
        #adminhome = AdminHome()
        #widget.addWidget(adminhome)
        #widget.setCurrentIndex(widget.currentIndex()+1)

    def adminloginfunction(self):
        global currUser, adminlst, customerlst
        
        adminID = self.adminfield.text()
        password = self.passwordfield.text()

        if len(adminID) == 0 or len(password) == 0:
            self.error.setText("Please input all fields.")

        else:
            try:
                conn = mysql.connect(
                    host = "localhost",
                    user = mySQLuser,
                    password = mySQLpw,
                    database = mySQLdb
                )

                cur = conn.cursor()
                query = 'SELECT password from administrators WHERE administratorID =\''+adminID+"\'"
                cur.execute(query)
                result_pass = cur.fetchone()[0]

                query1 = "SELECT * from administrators"
                cur.execute(query1)
                adminlst = list(cur.fetchall())

                query2 = "SELECT * from customers"
                cur.execute(query2)
                customerlst = list(cur.fetchall())


                # print(adminlst[0][1])
                if result_pass == password:
                    currUser = adminID
                    self.error.setText("")
                    print("Successfully logged in")
                    self.gotoadminhome()
                else:
                    self.error.setText("Invalid username or password")
            except:
                self.error.setText("Invalid username or password")



#class AdminHome(ProductScreen, CustomerLoginScreen):
class AdminHome(SearchScreen, CustomerLoginScreen):

    def __init__(self):

        super(AdminHome, self).__init__()
        loadUi("administratorloggedin.ui", self)
        
        self.admintable.setHorizontalHeaderLabels(["IID", "Category", "Model", "Number of 'SOLD' items", "Number of 'UNSOLD' items"])
        self.admintable.resizeColumnsToContents()
        self.admintable.resizeRowsToContents()
        self.admintable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.db.clicked.connect(lambda: self.inimysql())
        # self.inventre.clicked.connect(lambda: self.updateInventory())
        self.displaySalesBtn.clicked.connect(lambda: self.admindisplayfunction())
        self.back.clicked.connect(lambda: self.gotoadminlogin())
        self.search.clicked.connect(lambda: self.go2adminsearch())
        self.service.clicked.connect(lambda: self.gotoservice())

    
    def gotoservice(self):
        widget.setCurrentIndex(10)

    def go2adminsearch(self):
        widget.setCurrentIndex(9)

    # Placed this here cos search page no longer needs it.
    def updateInventory(self):
        _idList = products_collection.distinct('_id')

        for _id in _idList:
            pid2chk = products_collection.find({"_id":_id}, {"_id":0, "Category":1, "Model":1})
            # print(pid2chk[0])
            inv_filter = pid2chk[0]
            inv_filter["PurchaseStatus"] = "Unsold"
            unsold_count = items_collection.count_documents(inv_filter)

            #print(pid2chk[0])
            #print("Inventory:", unsold_count, "\n")
            products_collection.update_one({"_id":_id}, {"$set":{"Inventory":unsold_count}})
        print("Inventory updated")


    def inimysql(self):
        global currUser, mysqlorder

        
        dblist =[]
        tblist = []
        tblisto =[]
        dbflag = 1
        name = self.dbname.text()
        conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                passwd = mySQLpw
            )
        cur = conn.cursor()

        cur.execute("SHOW DATABASES")
        for dbn in cur:
            # name=tuple([name])
            dblist.append(dbn)
            # name = self.dbname.text()
            
        print("Searching through existing Databases...\n")
        # print(dblist)
        if tuple([name]) in dblist:
            print("Database Exists!\n")

            cur.execute("DROP DATABASE %s"%str(name))
            print("Dropping Database...")
            # cur.close()
            # print("Establishing Connection...\n")
            # conn = mysql.connect(
            #     host = "localhost",
            #     user = mySQLuser,
            #     passwd = mySQLpw,
            #     database = name
            # )

            cur = conn.cursor()
    

        else:
            # dbflag = 0
            print("Database Not Found...!\n")
        print("Creating Database...")
        cur.execute("CREATE DATABASE %s"% name)
        print("Database Successfully Initialised")

        conn.commit()
        
        def addtables():
            conn = mysql.connect(
                    host = "localhost",
                    user = mySQLuser,
                    passwd = mySQLpw,
                    database = name
                )
            cur = conn.cursor(buffered=True)

            # cluster = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false")
            # db = cluster["oshes"]
            # products_collection = db["products"]
            # items_collection = db["items"]


            results_p = products_collection.find()
            results_i = items_collection.find()


            # if dbflag == 0:
            print("Creating customers relation...")
            cur.execute("CREATE TABLE customers (customerID varchar(20) NOT NULL,customerName varchar(30) NOT NULL,customerFirstName varchar(20) NOT NULL,customerLastName varchar(10) NOT NULL,customerGender varchar(1) NOT NULL CHECK (customerGender IN ('M','F')),email varchar(50) NOT NULL,phone int(50) NOT NULL,addressLine1 varchar(50) NOT NULL,addressLine2 varchar(50) DEFAULT NULL,country varchar(50) NOT NULL,state varchar(50) DEFAULT NULL,city varchar(50) NOT NULL,postalCode varchar(15) NOT NULL,password varchar(50) NOT NULL,PRIMARY KEY (customerID))")
            
            sqlcus = "INSERT INTO customers VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.executemany(sqlcus, customerlst)

            # if dbflag == 0:
            print("Creating administrators relation...")
            cur.execute("CREATE TABLE administrators (administratorID varchar(20) NOT NULL,administratorName varchar(30) NOT NULL,administratorFirstName varchar(20) NOT NULL,administratorLastName varchar(10) NOT NULL,administratorGender varchar(1) NOT NULL,phone varchar(50) NOT NULL,password varchar(50) NOT NULL,PRIMARY KEY (administratorID))")

            sqladmin = "INSERT INTO administrators VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cur.executemany(sqladmin, adminlst)
                
            print("Creating products relation...")
            cur.execute("CREATE TABLE products (productID int(11) NOT NULL,category varchar(10) NOT NULL,model varchar(10) NOT NULL,`price ($)` int(10) NOT NULL,`cost ($)` int(10) NOT NULL,`warranty (months)` int(10) NOT NULL,inventory int(10) NOT NULL, PRIMARY KEY (productID))")
            
            print("Creating billings relation...")
            cur.execute("CREATE TABLE billings (billingID varchar(30) NOT NULL, purchaseDate Date NOT NULL, customerID varchar(20), PRIMARY KEY (billingID), FOREIGN KEY (customerID) REFERENCES customers(customerID))")

            print("Creating items relation...")

            cur.execute("CREATE TABLE items (itemID int(11) NOT NULL,category varchar(10) NOT NULL, model varchar(10) NOT NULL,color varchar(10) NOT NULL,factory varchar(20) NOT NULL,powersupply varchar(10) NOT NULL,productionyear varchar(10) NOT NULL,purchasestatus varchar(10) NOT NULL,servicestatus varchar(31) NOT NULL, billingID varchar(30), productID int(11), administratorID varchar(11), PRIMARY KEY (itemID),FOREIGN KEY (billingID) REFERENCES billings(billingID),FOREIGN KEY (productID) REFERENCES products(productID), FOREIGN KEY (administratorID) REFERENCES administrators(administratorID))")
            
            print("Creating requests relation...")
            cur.execute("CREATE TABLE requests (requestID int(11) AUTO_INCREMENT  NOT NULL,requestDate varchar(10) DEFAULT NULL, requestStatus varchar(33) DEFAULT NULL CHECK (requestStatus IN ('Submitted', 'Submitted and Waiting for payment', 'In progress','Approved','Cancelled','Completed')) ,serviceFee int(11) DEFAULT NULL,customerID varchar(20) NOT NULL,itemID int(11) NOT NULL,administratorID varchar(20) DEFAULT NULL,paymentDate Date DEFAULT NULL,paymentAmount int(15) DEFAULT 0, PRIMARY KEY (requestID),FOREIGN KEY (customerID) REFERENCES customers(customerID),FOREIGN KEY (itemID) REFERENCES items(itemID), FOREIGN KEY (administratorID) REFERENCES administrators(administratorID), UNIQUE(itemID))")
        # FOREIGN KEY (productID) REFERENCES products(productID), FOREIGN KEY (adminID) REFERENCES admininistrators(adminID)

            # i = 1
            self.updateInventory()
            for resultp in results_p:
                productid = resultp.get("ProductID")
                category = resultp.get("Category")
                model = resultp.get("Model")
                price = resultp.get("Price ($)")
                cost = resultp.get("Cost ($)")
                warranty = resultp.get("Warranty (months)")
                inventory = resultp.get("Inventory")

                sql = "INSERT INTO products (productID, category, model, `price ($)`,`cost ($)`, `warranty (months)`, inventory) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val= (str(productid),str(category), str(model), str(price), str(cost), str(warranty), int(inventory))
                # print("Inserted Product "+str(i)+" record")
                # i+=1
                cur.execute(sql,val)
            # conn.commit()

            # j =1
            for resulti in results_i:
                print(resulti)
                itemid = resulti.get("ItemID")
                category = resulti.get("Category")
                model = resulti.get("Model")

                fkeyall = products_collection.find_one({"Category": category, "Model":model})
                productidfkey = fkeyall["ProductID"]

                color = resulti.get("Color")
                factory = resulti.get("Factory")
                powersupply = resulti.get("PowerSupply")
                productionyear = resulti.get("ProductionYear")
                purchasestatus = resulti.get("PurchaseStatus")
                servicestatus = resulti.get("ServiceStatus")

                sqli = "INSERT INTO items (itemID, category, model, color, factory, powerSupply, productionYear, purchaseStatus, serviceStatus, productID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                vali= (str(itemid),str(category), str(model), str(color), str(factory), str(powersupply), str(productionyear), str(purchasestatus), str(servicestatus), str(productidfkey))
                # print("Inserted Item "+str(j)+" record")
                # j+=1
                cur.execute(sqli,vali)


            # sqlt ="INSERT INTO items(productID) VALUES (%s)" 
            # valt = "SELECT p.productID FROM products p, items i WHERE p.category = i.category AND p.model = i.model"
            # # print(valt)
            # cur.execute(valt)

            #fix this
            # foreignpidlist= []
            # for row in cur:
            #     rowint = str(''.join(map(str, row)))

            #     foreignpidlist.append(rowint)
            # print(len(foreignpidlist))
            # cur.executemany(sqlt, foreignpidlist)

            # print(foreignpidlist)

            # cur.execute("INSERT INTO items(productID) SELECT p.productID FROM products p, items i WHERE p.category = i.category AND p.model = i.model" )

            conn.commit()
            


        return addtables()

    def admindisplayfunction(self):
            
        # self.updateInventory()
        # print("Inventory Updated")
        
        # cluster = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false")
        # db = cluster["oshes"]
        # products_collection = db["products"]
        


        results = products_collection.find()


        for rowindex, details in enumerate(results):

            self.admintable.setRowCount(7)
            self.admintable.insertRow(7)
            self.admintable.setItem(rowindex, 0, QTableWidgetItem("00"+str(details["ProductID"])))
            self.admintable.setItem(rowindex, 1, QTableWidgetItem(details["Category"]))
            self.admintable.setItem(rowindex, 2, QTableWidgetItem(details["Model"]))

            inv_filter = {"Category":details["Category"], "Model":details["Model"]}
            inv_filter["PurchaseStatus"] = "Sold"
            sold_count = items_collection.count_documents(inv_filter)

            self.admintable.setItem(rowindex, 3, QTableWidgetItem(str(sold_count)))
            self.admintable.setItem(rowindex, 4, QTableWidgetItem(str(int(details["Inventory"]))))

       


        self.admintable.resizeColumnsToContents()
        self.admintable.resizeRowsToContents()



class RegisterScreen(CustomerLoginScreen):
    def __init__(self):
        super(RegisterScreen, self).__init__()
        loadUi("registration.ui", self)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)

        self.customerreg.clicked.connect(lambda: self.customerregfunction())
        self.adminreg.clicked.connect(lambda: self.adminregfunction())

        self.back.clicked.connect(lambda: self.gotowelcome())

    def showpopup(self):
        msg= QMessageBox()
        msg.setWindowTitle("Registration Status")
        msg.setText("Registration Successful!")
        msg.exec_()

    def customerregfunction(self):
        customerid = self.userid.text()
        name = self.fname.text() + " " + self.lname.text()
        fname = self.fname.text()
        lname = self.lname.text()
        gender = self.gender.text()
        email = self.email.text()
        phone = self.phone.text()
        address1 = self.address1.text()
        address2 = self.address2.text()
        country = self.country.text()
        state = self.state.text()
        city = self.city.text()
        postalcode = self.postalcode.text()
        password = self.password.text()
        
        if len(customerid) == 0 or len(name) == 0 or len(fname)==0 or len(lname)==0 or len(gender)==0 or len(email)==0 or len(phone)==0 or len(address1)==0 or len(country)==0 or len(city)==0 or len(postalcode)==0 or len(password)==0:
            self.error.setText("Please fill in all fields.")
        else:
            self.error.setText("")
            conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                passwd = mySQLpw,
                database = mySQLdb
            )
        
            cur = conn.cursor()
            user_info = [customerid, name, fname, lname, gender, email, phone, address1, address2, country, state, city, postalcode, password]
            sql = "INSERT INTO customers VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, user_info)
            conn.commit()

            self.showpopup()
            self.gotowelcome()

    def adminregfunction(self):
        adminid = self.userid.text()
        name = self.fname.text() + " " + self.lname.text()
        fname = self.fname.text()
        lname = self.lname.text()
        gender = self.gender.text()
        phone = self.phone.text()
        password = self.password.text()
        authcode = self.authcode.text()

        if len(adminid) == 0 or len(name) == 0 or len(fname)==0 or len(lname)==0 or len(gender)==0 or len(phone)==0 or len(password)==0:
            self.error.setText("Please fill in all fields.")
        elif authcode != "1234":
            self.error.setText("Authentication failed.")
        else:
            self.error.setText("")
            conn = mysql.connect(
                host = "localhost",
                user = mySQLuser,
                password = mySQLpw,
                database = mySQLdb
            )

            curr = conn.cursor()
            admin_info = [adminid, name, fname,lname, gender, phone, password]
            sql = "INSERT INTO administrators VALUES (%s, %s, %s, %s, %s, %s, %s)"
            curr.execute(sql, admin_info)
            conn.commit()

            self.showpopup()
            self.gotowelcome()
            
            
# class billing(ProductScreen):
#     def __init__(self):
#         super(billing,self).__init__()
#         loadUi("request.ui", self)
#         self.addtobilling()

#     def addtobilling(self):
#         self.add2cartBtn()



if __name__ == "__main__":
    app         = QApplication(sys.argv)
    welcome     = WelcomeScreen()
    register    = RegisterScreen()
    login       = CustomerLoginScreen()
    adminlogin  = AdminLoginScreen()
    adminhome   = AdminHome()
    search      = SearchScreen()
    cart        = CartScreen()
    purchasehistory    = PurchaseHistoryScreen()
    reqcartscreen = reqCartScreen()
    adminsearch = AdminSearchScreen()
    service = serviceScreen()

    widget = QStackedWidget()           # widgetIndex
    widget.addWidget(welcome)           # 0
    widget.addWidget(register)          # 1
    widget.addWidget(login)             # 2
    widget.addWidget(adminlogin)        # 3
    widget.addWidget(adminhome)         # 4
    widget.addWidget(search)            # 5
    widget.addWidget(cart)              # 6
    widget.addWidget(purchasehistory)   # 7
    widget.addWidget(reqcartscreen)     # 8
    widget.addWidget(adminsearch)       # 9 
    widget.addWidget(service)           # 10



    widget.setFixedHeight(640)
    widget.setFixedWidth(980)
    widget.show()
    try:
        sys.exit(app.exec_())
        
    except:
        print("Exiting")