from transformation_app.data_transformation_contratos_secop import get_contracts_summary, get_unique_bpins

def test_functions():
    print("="*60)
    print("TESTING CONTRATOS FUNCTIONS")
    print("="*60)
    
    try:
        # Test summary function
        summary = get_contracts_summary()
        print("RESUMEN DE CONTRATOS:")
        print(f"Total contratos: {summary['total_contracts']:,}")
        print(f"BPINs únicos: {summary['unique_bpins']:,}")
        print(f"Entidades únicas: {summary['unique_entities']:,}")
        print(f"Valor total: ${summary['total_contract_value']:,.2f}")
        print(f"Valor promedio: ${summary['average_contract_value']:,.2f}")
        print(f"Rango de fechas: {summary['date_range']['earliest']} a {summary['date_range']['latest']}")
        
        print("\nTop 5 estados de contratos:")
        for state, count in list(summary['contract_states'].items())[:5]:
            print(f"  - {state}: {count}")
        
        print("\nTop 5 tipos de contratos:")
        for ctype, count in list(summary['contract_types'].items())[:5]:
            print(f"  - {ctype}: {count}")
            
        # Test unique BPINs function
        unique_bpins = get_unique_bpins()
        print(f"\nPrimeros 10 BPINs únicos:")
        for bpin in unique_bpins[:10]:
            print(f"  - {bpin}")
            
        print("\nTodas las funciones funcionan correctamente!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_functions()
