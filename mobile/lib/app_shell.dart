import 'package:flutter/material.dart';
import 'app_theme.dart';
import 'services/api_service.dart';
import 'screens/dashboard_screen.dart';
import 'screens/fields_screen.dart';
import 'screens/weather_screen.dart';
import 'screens/disease_scanner_screen.dart';
class FarmDashboard extends StatefulWidget {
  const FarmDashboard({super.key, this.api = const ApiService()});

  final ApiService api;
  @override
  State<FarmDashboard> createState() => _FarmDashboardState();
}

class _FarmDashboardState extends State<FarmDashboard> {
  int selectedIndex = 0;
  bool loading = true;
  String? error;
  List<Map<String,dynamic>> fields = [];
  int? selectedFieldId;
  Map<String,dynamic>? field, crop, soil, irrigation, weather, hourly;

  @override
  void initState() { super.initState(); loadFields(); }

  Future<Map<String,dynamic>> getObject(String path) async {
    return widget.api.getObject(path);
  }
  Future<List<Map<String,dynamic>>> getList(String path) async {
    return widget.api.getList(path);
  }
  Future<void> loadFields() async {
    setState(() { loading = true; error = null; });
    try {
      // Farm 1 is the existing demo farm returned by this project's database.
      final result = await getList('/api/v1/fields/farm/$demoFarmId');
      if (result.isEmpty) throw Exception('No fields are registered under demo farm $demoFarmId yet.');
      fields = result;
      selectedFieldId ??= (result.first['id'] as num).toInt();
      if (!fields.any((f)=>(f['id'] as num).toInt()==selectedFieldId)) selectedFieldId=(result.first['id'] as num).toInt();
      await loadSelectedField(showSpinner: false);
      if (mounted) setState(() { loading = false; error = null; });
    } catch (e) {
      if (mounted) setState(() { loading = false; error = friendlyError(e); });
    }
  }
  Future<void> loadSelectedField({bool showSpinner = true}) async {
    final id = selectedFieldId;
    if (id == null) return;
    if (showSpinner && mounted) setState(() { loading = true; error = null; });
    try {
      final f = await getObject('/api/v1/fields/$id');
      final results = await Future.wait<dynamic>([
        getList('/api/v1/crops/field/$id'), getList('/api/v1/soil/field/$id'),
        getObject('/api/v1/recommendations/irrigation/$id')]);
      final crops = results[0] as List<Map<String,dynamic>>;
      final soils = results[1] as List<Map<String,dynamic>>;
      Map<String,dynamic>? w, h; String? weatherError;
      try {
        final lat = f['latitude']; final lon = f['longitude'];
        if (lat is num && lon is num) {
          final wx = await Future.wait<Map<String,dynamic>>([
            getObject('/api/v1/weather/current?latitude=$lat&longitude=$lon'),
            getObject('/api/v1/weather/hourly?latitude=$lat&longitude=$lon')]);
          w=wx[0]; h=wx[1];
        } else { weatherError = 'Field coordinates are missing.'; }
      } catch (e) { weatherError = friendlyError(e); }
      if (!mounted) return;
      setState(() {
        field=f;
        final activeCrops = crops.where((c) => '${c['status']}'.toUpperCase() == 'ACTIVE').toList();
        crop = activeCrops.isNotEmpty ? activeCrops.first : (crops.isNotEmpty ? crops.first : null);
        soil=soils.isNotEmpty ? soils.first : null; irrigation=results[2] as Map<String,dynamic>;
        weather=w; hourly=h; loading=false; error=null;
        if (weatherError != null && w == null) error = 'Field data loaded. Weather unavailable: $weatherError';
      });
    } catch (e) {
      if (mounted) setState(() { loading=false; error=friendlyError(e); });
    }
  }
  String friendlyError(Object e) => friendlyApiError(e);
  void chooseField(int? id) { if (id==null) return; setState(() { selectedFieldId=id; }); loadSelectedField(); }
  @override
  Widget build(BuildContext context) {
    final titles=['AI Farm Copilot','My Fields','Disease Scanner','Weather'];
    final pages=<Widget>[
      HomePage(loading:loading,error:error,fields:fields,selectedFieldId:selectedFieldId,field:field,crop:crop,soil:soil,irrigation:irrigation,weather:weather,onFieldChanged:chooseField,onRefresh:loadFields,onScan:()=>setState(()=>selectedIndex=2)),
      FieldsPage(loading:loading,error:error,fields:fields,selectedFieldId:selectedFieldId,field:field,crop:crop,soil:soil,onSelect:chooseField,onRefresh:loadFields),
      const DiseaseScannerPage(),
      WeatherPage(loading:loading,error:error,field:field,weather:weather,hourly:hourly,onRefresh:loadFields),
    ];
    return Scaffold(appBar:AppBar(title:Row(children:[const Icon(Icons.eco,size:27),const SizedBox(width:9),Flexible(child:Text(titles[selectedIndex],style:const TextStyle(fontWeight:FontWeight.bold),overflow:TextOverflow.ellipsis))]),actions:[IconButton(tooltip:'Refresh data',onPressed:loading?null:loadFields,icon:const Icon(Icons.refresh)),const SizedBox(width:8)]),
      body:SafeArea(child:IndexedStack(index:selectedIndex,children:pages)),
      bottomNavigationBar:NavigationBar(selectedIndex:selectedIndex,onDestinationSelected:(i)=>setState(()=>selectedIndex=i),destinations:const [NavigationDestination(icon:Icon(Icons.dashboard_outlined),selectedIcon:Icon(Icons.dashboard),label:'Home'),NavigationDestination(icon:Icon(Icons.grass_outlined),selectedIcon:Icon(Icons.grass),label:'Fields'),NavigationDestination(icon:Icon(Icons.document_scanner_outlined),selectedIcon:Icon(Icons.document_scanner),label:'Scan'),NavigationDestination(icon:Icon(Icons.cloud_outlined),selectedIcon:Icon(Icons.cloud),label:'Weather')]));
  }
}
