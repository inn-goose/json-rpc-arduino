#include <ArduinoJson.h>

static const unsigned long SERIAL_BAUD = 115200;

// balance between the protocol throughput and the board memory limit
static const int JSON_RPC_BUFFER_SIZE = 512;
static char json_rpc_buffer[JSON_RPC_BUFFER_SIZE];
static int json_rpc_buffer_pos = 0;

// TODO: use \0 for the CLI
#define END_OF_JSON_RPC_MESSAGE '\n'


void send_result(int32_t id, const char* result_message) {
  // {"jsonrpc":"2.0","id":-,"result":""}
  // base lenght is 36
  // +10 for ID (max signed 32 len)
  // 46 in total
  DynamicJsonDocument response(46 + strlen(result_message));
  response["jsonrpc"] = "2.0";
  response["id"] = id;

  response["result"] = result_message;

  serializeJson(response, Serial);
  response.clear();
  response.garbageCollect();

  Serial.write(END_OF_JSON_RPC_MESSAGE);
  Serial.flush();
}


void send_error(int32_t id, int32_t error_code, const char* error_message, const char* error_data) {
  // {"jsonrpc":"2.0","id":-,"error":{"code":-,"message":"","data":""}}
  // base lenght is 66
  // +10 for ID (max signed 32 len)
  // +10 for error_code
  // 86 in total
  DynamicJsonDocument response(86 + strlen(error_message) + strlen(error_data));
  response["jsonrpc"] = "2.0";
  response["id"] = id;

  JsonObject error = response.createNestedObject("error");
  error["code"] = error_code;
  error["message"] = error_message;
  if (error_data != 0) {
    error["data"] = error_data;
  }

  serializeJson(response, Serial);
  response.clear();
  response.garbageCollect();

  Serial.write(END_OF_JSON_RPC_MESSAGE);
  Serial.flush();
}


bool get_params_int32(JsonObject params, const char* key, int32_t& out) {
  if (!params.containsKey(key)) return false;
  if (!params[key].is<int32_t>()) return false;
  out = params[key].as<int32_t>();
  return true;
}


void process_request(JsonDocument& request) {
  // validata JSON RPC format
  if (!request.containsKey("jsonrpc") || strcmp(request["jsonrpc"], "2.0") != 0) {
    send_error(0, -32600, "Invalid Request", "Invalid protocol version");
    return;
  }

  int32_t id = request.containsKey("id") ? request["id"].as<int32_t>() : 0;

  const char* method = request["method"] | "";
  JsonVariant params = request["params"];

  if (strcmp(method, "set_builtin_led") == 0) {
    if (!params.is<JsonObject>()) {
      send_error(id, -32602, "Invalid params", "Object expected");
      return;
    }

    int32_t status = 0;
    if (!get_params_int32(params, "status", status)) {
      send_error(id, -32602, "Invalid params", "Invalid status");
      return;
    }

    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, status ? HIGH : LOW);

    send_result(id, status ? "OK: builtin LED is ON" : "OK: builtin LED is OFF");
  } else {
    send_error(id, -32601, "Method not found", method);
  }
}


void setup() {
  Serial.begin(SERIAL_BAUD);
}


void loop() {
  // waiting for the data and read by char
  while (Serial.available()) {
    char c = (char)Serial.read();

    if (c == END_OF_JSON_RPC_MESSAGE) {
      DynamicJsonDocument request(json_rpc_buffer_pos);
      DeserializationError deserialization_error = deserializeJson(request, json_rpc_buffer, json_rpc_buffer_pos);
      if (deserialization_error) {
        const char* error_data = deserialization_error.c_str();
        send_error(0, -32700, "Parse error", error_data);
      } else {
        process_request(request);
      }
      request.clear();
      request.garbageCollect();
      json_rpc_buffer_pos = 0;
      return;
    }

    // buffer overflow
    if (json_rpc_buffer_pos >= JSON_RPC_BUFFER_SIZE) {
      send_error(0, -32600, "Invalid Request", "JSON RPC message is to large");
      json_rpc_buffer_pos = 0;
      return;
    }

    // read next char
    json_rpc_buffer[json_rpc_buffer_pos++] = c;
  }
}