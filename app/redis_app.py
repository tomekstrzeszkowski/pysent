import time
from redis import RedisError, sentinel, ReadOnlyError
import sys

ERROR_KEY_NOT_FOUND = "Key not found in redis"


class RedisDriver:
    def __init__(self, redis_config):
        self.service = redis_config["service_name"]
        self.__connect(redis_config)

    def __connect(self, redis_config):
        self.connection = sentinel.Sentinel(
            [
                (redis_config["sentinel_host"], redis_config["sentinel_port"]),
            ],
            socket_timeout=0.5,
        )
        # print(self.connection.master_for("mymaster"))
        # print(self.connection.discover_slaves("mymaster"))

    def set(self, key, value):
        key_str = str(key)
        val_str = str(value)
        try:
            master = self.connection.master_for(self.service)
            master.set(key_str, val_str)
            return {"success": True}
        except RedisError as err:
            error_str = "Error while connecting to redis : " + str(err)
            return {"success": False, "error": error_str}

    def get(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = master.get(key_str)
        except RedisError as err:
            error_str = "Error while retrieving value from redis : " + str(err)
            return {"success": False, "error": error_str}

        if value is not None:
            return {"success": True, "value": value}
        else:
            return {"success": False, "error": ERROR_KEY_NOT_FOUND}

    def delete(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = master.delete(key_str)
        except RedisError as err:
            error_str = "Error while deleting key from redis : " + str(err)
            return {"success": False, "error": error_str}

        return {"success": True}


if __name__ == "__main__":
    print("*" * 75)
    redis_config = {
        "service_name": "mymaster",
        "sentinel_host": "sentinel-1",
        "sentinel_port": 26379,
    }

    redis_driver = RedisDriver(redis_config)
    while True:
        result = redis_driver.set("hello", "world")
        print(result)

        if result["success"]:
            result = redis_driver.get("hello")
            print(result)

        slave = redis_driver.connection.slave_for(redis_driver.service)
        try:
            slave.set("slave", "slave")
        except ReadOnlyError:
            print("Slave is readonly")
        print("******** SLEEPING *********")
        time.sleep(10)

        print("******** AGAIN *********")
        result = redis_driver.set("hello2", "world2")
        print(result)

        if result["success"]:
            result = redis_driver.get("hello2")
            print(result)
        redis_driver.delete("hello")
        time.sleep(10)
