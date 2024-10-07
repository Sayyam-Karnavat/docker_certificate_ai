

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from artifact import HelloWorldClient
import base64
from algosdk import account, mnemonic , transaction


class CertificateBlockchain:

    def __init__(self) -> None:

        # Client initialization
        self.algod_address = "https://testnet-api.algonode.cloud"
        self.algod_token = "a" * 64
        self.indexer_add = "https://testnet-idx.algonode.cloud"
        self.algod_client = AlgodClient(self.algod_token, self.algod_address)
        self.indexer_client = IndexerClient("", self.indexer_add)


        # Deployer initialization and funding
        # self.deployer_private_key , self.deployer_wallet_address = account.generate_account()
        # self.deployer_mnemonic = mnemonic.from_private_key(self.deployer_private_key)
        # self.deployer = algokit_utils.get_account_from_mnemonic(self.deployer_mnemonic)
        self.deployer_private_key = "eywhxVYJht8aukUhXLiUp7LHP6Eb6QzZKegGRxRiEWQXcoHThaOdjs3WpQEO49+L5jXouZ5wG3wzXSwzIxAP3Q=="
        self.deployer_wallet_address = "C5ZIDU4FUOOY5TOWUUAQ5Y67RPTDL2FZTZYBW7BTLUWDGIYQB7O4WPPJHA"
        self.deployer_mnemonic = "month lucky glad nice army retire speak east loud thumb ski clerk month exit tackle trouble canoe polar inject idea chuckle flat calm about mango"
        self.deployer = algokit_utils.get_account_from_mnemonic(self.deployer_mnemonic)
        # Client creation
        self.app_client = HelloWorldClient(
            self.algod_client,
            creator=self.deployer,
            indexer_client=self.indexer_client,
        )

        self.app_client.app_id = 722609496

        
        ####  Contract is already deployed on Testnet  and funded ####
        # self.deploy_contract()
        print("Contract deployed on APP :-" , self.app_client.app_id)


    def get_deployer_details(self):
        print(f"Deployer wallet address :- {self.deployer_wallet_address}")
        print(f"Deployer private key :- {self.deployer_private_key}")
        print(f"Deployer mnemonic :- {self.deployer_mnemonic}")

    def deploy_contract(self):
        self.fund_account(deployer_address = self.deployer_wallet_address)
        self.app_client.deploy(
            on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
            on_update=algokit_utils.OnUpdate.AppendApp,
        )

    
    def write_to_blockchain(self, pdf_hash="" , ocr_hash=""):
        try:
            if not pdf_hash and not ocr_hash:
                raise Exception("Provide some data besides NULL data")
            response = self.app_client.write_certificate_data(pdf_extracted_text_hash= f"{pdf_hash}" , OCR_extracted_text_hash= f"{ocr_hash}")
            return response.tx_id
        except Exception as e:
            print("Error writing data to blockchain " , str(e))
            return 0

    def check_pdf_hash_existence(self , hash_to_check):

        response  = self.indexer_client.search_transactions_by_address(address= self.deployer_wallet_address)
        all_transactions = response['transactions']


        for single_transaction in all_transactions:
            if "global-state-delta" in single_transaction:
                global_state_delta = single_transaction['global-state-delta']
                for single_delta in global_state_delta:
                    attribute = single_delta['key']
                    value = single_delta['value']['bytes']

                    print(f"{attribute} - {value}" )

                    if attribute == "pdf_data_hash" and value == hash_to_check:
                        return 1
        return 0
    
    def check_ocr_hash_existence(self , hash_to_check):
        response  = self.indexer_client.search_transactions_by_address(address= self.deployer.address)
        all_transactions = response['transactions']
        for single_transaction in all_transactions:
            if "global-state-delta" in single_transaction:
                global_state_delta = single_transaction['global-state-delta']
                for single_delta in global_state_delta:
                    if 'key' in single_delta and "value" in single_delta and 'bytes' in single_delta['value']:
                        attribute = single_delta['key']
                        value = single_delta['value']['bytes']
                        decoded_attribute = base64.b64decode(attribute).decode("utf-8")
                        decoded_value = base64.b64decode(value).decode("utf-8")
                        if decoded_attribute == "ocr_data_hash" and decoded_value == hash_to_check:
                            return 1
        return 0
    
    def fund_account(self , deployer_address):
        self.master_private_key = mnemonic.to_private_key(mnemonic="banner enlist wide have awake rail resource antique arch tonight pilot abuse file metal canvas beyond antique apart giant once slight ice beef able uncle")
        self.master_wallet_address = account.address_from_private_key(private_key=self.master_private_key)

        self.amount_microalgos = int(1 * 1e6)

        self.suggested_params = self.algod_client.suggested_params()

        self.txn = transaction.PaymentTxn(
            sender= self.master_wallet_address,
            receiver= self.deployer_wallet_address,
            amt= self.amount_microalgos,
            sp=self.suggested_params,
        )

        self.signed_txn = self.txn.sign(private_key=self.master_private_key)
        self.txid = self.algod_client.send_transaction(self.signed_txn)
        print(f"Account {deployer_address} funded  with {self.amount_microalgos} !!!")


if __name__ == "__main__":
    obj = CertificateBlockchain()
    # transaction_id = obj.write_to_blockchain(ocr_hash="sample_hash")
    # print("Hash written :-" , transaction_id)
    res = obj.check_ocr_hash_existence(hash_to_check="sample_hash123")
    print(res)
    
