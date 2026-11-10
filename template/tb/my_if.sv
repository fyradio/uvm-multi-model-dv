// my_if.sv — 凍結的 DUT interface（FROZEN，範例，依你的 DUT 修改後再凍結）
interface my_if (input logic clk, input logic rst_n);
  logic        valid, ready, wr;
  logic [7:0]  addr;
  logic [31:0] wdata, rdata;
endinterface
