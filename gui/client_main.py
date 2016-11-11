from PyQt4.QtGui import *
from PyQt4 import Qt
from client_sec import *

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("images/SECURED_logo.png"))
#app.setStyle("cleanlooks")
#app.setStyle("cde")
app.setStyle("mac")

ghui = GUI() 
sys.exit(app.exec_())
