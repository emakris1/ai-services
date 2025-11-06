import 'dart:io';
import 'dart:convert';
import 'package:app/cubits/action_mapping_cubit.dart';
import 'package:flutter/services.dart' show rootBundle;

const String mappingsFileLocation = 'assets/action_mappings.json';

class ActionMappingRepository {
  Future<Map<String, dynamic>> _loadJson() async {
    final jsonString = await rootBundle.loadString(mappingsFileLocation);
    return jsonDecode(jsonString) as Map<String, dynamic>;
  }

  Future<void> _saveJson(Map<String, dynamic> data) async {
    final file = File(mappingsFileLocation);
    final encoder = const JsonEncoder.withIndent('  ');
    final prettyString = encoder.convert(data);

    await file.writeAsString(prettyString);
  }

  ActionMapping fromDomain(Map<String, dynamic> data) {
    ActionMapping mapping = {};

    data.forEach((actorName, actionPhraseMapRaw) {
      Actor actor = Actor.values.byName(actorName.split('.').last);

      final actionPhraseMap = <String, List<String>>{};
      (actionPhraseMapRaw as Map<String, dynamic>).forEach((
        action,
        phrasesRaw,
      ) {
        actionPhraseMap[action] = List<String>.from(
          phrasesRaw as List<dynamic>,
        );
      });

      mapping[actor] = actionPhraseMap;
    });

    return mapping;
  }

  Map<String, dynamic> toDomain(ActionMapping mapping) {
    Map<String, ActionPhraseMap> data = {};

    mapping.forEach((actor, actionPhraseMap) {
      String actorName = actor.toString();
      data[actorName] = actionPhraseMap;
    });

    return data;
  }

  Future<ActionMapping> read() async {
    final data = await _loadJson();
    return fromDomain(data);
  }

  Future<void> write(ActionMapping mapping) async {
    Map<String, dynamic> data = toDomain(mapping);
    return await _saveJson(data);
  }
}
