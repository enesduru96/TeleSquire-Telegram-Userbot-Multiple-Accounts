import os
import time

import xml.etree.ElementTree as ET
import os
import xml.dom.minidom as minidom

import subprocess


class ProxifierSetter:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.profile_path = os.path.join(self.base_dir, "Proxifier", "Profiles", "Default.ppx")
        self.proxies_file = os.path.join(self.base_dir, "my_proxies.txt")
        self.webshare_api_key = "ngobgxk9bf2ofua19kmj71t73bugvf3jb07lojtv"

    def restart_proxifier(self):
        subprocess.run(["taskkill", "/F", "/IM", "Proxifier.exe"])
        time.sleep(2)
        proxifier_exe = os.path.join(self.base_dir, "Proxifier", "Proxifier.exe")
        subprocess.Popen([proxifier_exe], creationflags=subprocess.DETACHED_PROCESS)
        time.sleep(5)

    def update_proxifier(self):
        with open(self.proxies_file,"r",encoding="utf-8") as f:
            proxy_list = [line for line in f.read().splitlines()]

        tree = ET.parse(self.profile_path)
        root = tree.getroot()

        proxy_list_element = root.find("ProxyList")
        proxy_list_element.clear()

        proxy_id = 102
        encrypted_password = "AAAClqQCmxzZgFDHWk//rM44EpLShOg9m5I/ChWPLJPWpCk="

        for proxy in proxy_list:
            host, port, user, _ = proxy.split(":")

            proxy_element = ET.SubElement(proxy_list_element, "Proxy", id=str(proxy_id), type="SOCKS5")
            
            auth_element = ET.SubElement(proxy_element, "Authentication", enabled="true")
            username_element = ET.SubElement(auth_element, "Username")
            username_element.text = user
            password_element = ET.SubElement(auth_element, "Password")
            password_element.text = encrypted_password

            options_element = ET.SubElement(proxy_element, "Options")
            options_element.text = "48"
            port_element = ET.SubElement(proxy_element, "Port")
            port_element.text = port
            address_element = ET.SubElement(proxy_element, "Address")
            address_element.text = host

            proxy_id += 1
            
        xml_str = ET.tostring(root, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ", newl='\n')


        with open(self.profile_path, "w", encoding="utf-8") as f:
            for line in pretty_xml.splitlines():
                if line.strip():
                    f.write(line + "\n")
        
        self.restart_proxifier()


    def get_next_proxy_LDPlayer(self):
        tree = ET.parse(self.profile_path)
        root = tree.getroot()
        start_value = 102
        max_value = 201

        for rule in root.findall('.//RuleList/Rule'):
            name = rule.find('Name')
            if name is not None and name.text == 'Default':
                action = rule.find('Action')
                if action is not None and action.get('type') == 'Proxy':
                    current_value = int(action.text)
                    if current_value < max_value:
                        new_value = current_value + 1
                    else:
                        new_value = start_value
                    action.text = str(new_value)

                    for proxy in root.findall('.//ProxyList/Proxy'):
                        if proxy.get('id') == new_value:
                            address = proxy.find('Address').text
                            port = proxy.find('Port').text
                            username = proxy.find('Authentication/Username').text
                            password = "e8lo7czgg2mf"
                            proxy_info = f"{address}:{port}:{username}:{password}"
                            break
                    break


        xml_str = ET.tostring(root, encoding="utf-8")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ", newl='\n')

        with open(self.profile_path, "w", encoding="utf-8") as f:
            for line in pretty_xml.splitlines():
                if line.strip():
                    f.write(line + "\n")
        
        self.restart_proxifier()
        return proxy_info