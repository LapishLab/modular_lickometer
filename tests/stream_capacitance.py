from capacitance import get_SipperArray_instance
import time

def main():
	sippers = get_SipperArray_instance()
	while True:
		(l, l_ref) = sippers.left.read()
		(r, r_ref) = sippers.right.read()
		print(f'L1:{l}, L2:{l_ref}, R1:{r}, R2:{r_ref}')
		time.sleep_ms(10)
		

if __name__ == "__main__":
	main()