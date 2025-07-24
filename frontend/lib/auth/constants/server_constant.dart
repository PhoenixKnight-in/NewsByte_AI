import 'dart:io';
class ServerConstant {
  //static const String serverURL = "http://172.17.180.87:8000";
  static String serverURL = Platform.isAndroid ?"http://10.0.2.2:8000" :"http://172.17.180.87:8000" ;
}
 