import hashlib
import os
import shutil
from collections import defaultdict

from scapy.all import rdpcap, wrpcap


class PcapProcessor:
    def __init__(self, analysis_report_dir, dump_pcap, pcap_dir, flow_dir, bytes_dir):
        # input path
        self.ANALYSIS_REPORT_DIR = analysis_report_dir
        self.DUMP_PCAP = dump_pcap
        # output path
        self.PCAP_DIR = pcap_dir
        self.FLOW_DIR = flow_dir
        self.BYTES_DIR = bytes_dir

    def access_pcap_report(
        self,
        file_name,
        task_id,
    ):
        """
        Get report and save as json file
        """
        source_file_path = os.path.join(
            self.ANALYSIS_REPORT_DIR, str(task_id), self.DUMP_PCAP
        )
        destination_path = os.path.join(self.PCAP_DIR, f"{file_name}.pcap")
        shutil.copy(source_file_path, destination_path)

    def extract_flows(self, file_name):
        """ """
        input_pcap_path = os.path.join(self.PCAP_DIR, file_name)
        packets = rdpcap(input_pcap_path)
        # Use dict to store pkt info to avoid duplication
        flows = defaultdict(list)
        for pkt in packets:
            # Filter: 1. with IP 2: with TCP or UDP
            if "IP" in pkt and (pkt.haslayer("TCP") or pkt.haslayer("UDP")):
                flow_key = (
                    pkt["IP"].src,
                    pkt.sport if pkt.haslayer("TCP") else pkt["UDP"].sport,
                    pkt["IP"].dst,
                    pkt.dport if pkt.haslayer("TCP") else pkt["UDP"].dport,
                    "TCP" if pkt.haslayer("TCP") else "UDP",
                )
                if flow_key in flows:
                    # TODO: How to process duplicated flow_key?
                    print("Duplicate flow found:", flow_key)
                flows[flow_key].append(pkt)
        return flows

    def write_flows_to_pcap(self, sample_file_name, flows):
        """ """
        output_pcap_dir = os.path.join(
            self.FLOW_DIR, os.path.splitext(sample_file_name)[0]
        )
        os.makedirs(output_pcap_dir, exist_ok=True)
        for flow_key, packets in flows.items():
            file_name = f"{flow_key[0]}_{flow_key[1]}_{flow_key[2]}_{flow_key[3]}_{flow_key[4]}.pcap"
            output_pcap_path = os.path.join(output_pcap_dir, file_name)
            wrpcap(output_pcap_path, packets)

    def generate_hash_name(self, pcap_file):
        with open(pcap_file, "rb") as f:
            file_content = f.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        return f"{file_hash}.txt"

    def remove_address(self, pkt):
        if "IP" in pkt:
            pkt["IP"].src = "0.0.0.0"
            pkt["IP"].dst = "0.0.0.0"
        if "TCP" in pkt:
            pkt["TCP"].sport = 0
            pkt["TCP"].dport = 0
        if "UDP" in pkt:
            pkt["UDP"].sport = 0
            pkt["UDP"].dport = 0
        return pkt

    def pad_data(self, data, target_length):
        current_length = len(data)
        if current_length >= target_length:
            return data[:target_length]
        else:
            padding_length = target_length - current_length
            padding_data = b"\x00" * padding_length
            return data + padding_data

    def trans_to_bytes(self, input_pcap_path, output_dir):
        packets = rdpcap(input_pcap_path)
        output_file_path = os.path.join(
            output_dir, self.generate_hash_name(input_pcap_path)
        )
        filtered_packets = [self.remove_address(pkt) for pkt in packets]
        bytes_data = [bytes_data(pkt) for pkt in filtered_packets]
        combined_bytes = b"".join(bytes_data)
        padded_bytes = self.pad_data(combined_bytes, 28 * 28 * 8)
        with open(output_file_path, "wb") as f:
            f.write(b"".join(padded_bytes))

    def extract_bytes(self, folder_name):
        input_dir = os.path.join(self.FLOW_DIR, folder_name)
        input_pcap_files = os.listdir(input_dir)
        output_dir = os.path.join(self.BYTES_DIR, folder_name)
        for pcap_file in input_pcap_files:
            input_path = os.path.join(input_dir, pcap_file)
            self.trans_to_bytes(input_path, output_dir)