import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('config.ini')

class Config:
    def __init__(self, section_name):
    	self.section_name = section_name
    	if not config.has_section(section_name):
    		config.add_section(section_name)
    		self.save()

    def save(self):
    	with open('config.ini', 'wb') as configfile:
    		config.write(configfile)

    def all(self):
    	return config.items(self.section_name)

    def get(self, key, default=None):
        try:
            result = config.get(self.section_name, key)
        except:
            result = default
    	return result or default 

    def set(self, key, value):
    	config.set(self.section_name, key, value)
    	self.save()
    
    def __getitem__(self, key):
    	return self.get(key)

    def __setitem__(self, key, value):
    	self.set(key, value)

