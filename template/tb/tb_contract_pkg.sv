// ============================================================================
// tb_contract_pkg.sv  —  凍結的介面合約（FROZEN）
// 由人或主模型(A)在分工前寫好。其他模型只能 import 使用，不得修改。
// 要改：開 open question，裁決後由 A 改，並把 contract_version +1。
// ============================================================================
`ifndef TB_CONTRACT_PKG_SV
`define TB_CONTRACT_PKG_SV

package tb_contract_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  localparam string CONTRACT_VERSION = "1";
  localparam int    ADDR_W = 8;
  localparam int    DATA_W = 32;

  typedef enum bit { RD = 0, WR = 1 } op_e;

  // ---- 唯一的 transaction 定義 ----
  class my_item extends uvm_sequence_item;
    rand op_e               op;
    rand bit [ADDR_W-1:0]   addr;
    rand bit [DATA_W-1:0]   data;
    `uvm_object_utils_begin(my_item)
      `uvm_field_enum(op_e, op, UVM_ALL_ON)
      `uvm_field_int (addr,     UVM_ALL_ON)
      `uvm_field_int (data,     UVM_ALL_ON)
    `uvm_object_utils_end
    function new(string name = "my_item"); super.new(name); endfunction
  endclass

  // ---- Reference model 的固定簽名（C 模型與 D 模型各自獨立實作）----
  virtual class ref_model_base extends uvm_object;
    function new(string name = "ref_model_base"); super.new(name); endfunction
    // 輸入一筆 transaction，回傳預期輸出（讀才有意義）
    pure virtual function bit [DATA_W-1:0] predict(my_item t);
    pure virtual function void reset();
  endclass

  // ---- 需求追蹤：每個檢查點都必須用這兩個 macro 回報 REQ 編號 ----
  // gate.py 會掃 log：每個 REQ 至少要有一次 PASS，而且不能出現 vplan 沒有的 REQ。
  `define REQ_PASS(id, msg) `uvm_info("REQCHK", $sformatf("%s PASS %s", id, msg), UVM_LOW)
  `define REQ_FAIL(id, msg) `uvm_error("REQCHK", $sformatf("%s FAIL %s", id, msg))

endpackage

`endif
