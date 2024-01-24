from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from surfacecode.nodes import ZNode, XNode, DataNode, BaseNode, FlagNode, AncillaNode
from surfacecode.lattice import SquareLattice, HeavyHexLattice
from surfacecode.circuits import ConstrainedQuantumCircuit

class BaseCycle:
    def __init__(self, lattice):
        self.lattice = lattice
        self.num_nodes = len(lattice.nodes)

    def _circuit():
        pass


class SurfaceCodeCycle(BaseCycle):
    """
    QuantumCircuit builder for surface code constrained by the given SquareLattice
    """
    def __init__ (self, lattice):
        assert isinstance(lattice, SquareLattice)
        super().__init__(lattice)

    def _circuit(self, num_cycles=1):
        """
        Returns the surface code QuantumCircuit depending on the number of cycles specified
        :param num_cycles: Number of full cycles the surface code will be runned.
        """
        num_nodes = self.num_nodes
        qc = ConstrainedQuantumCircuit(self.lattice, num_nodes)


        for j in range(num_cycles):
            # For every cycle add a classical register so we can track the changes in the surface code
            qc.add_register(ClassicalRegister(num_nodes))

            # Iterate through names of nodes in square lattice
            # TODO Change lattice.node structure to contain tuples or be a dictionary
            for i in self.lattice.graph.keys():
                node = self.lattice.nodes[i]
                classicalBitLoc = i + j * num_nodes

                # If node is ZNode add measure_z circuit cycle
                if type(node) == ZNode:
                    qc.append(self._measure_z(i), range(num_nodes), [classicalBitLoc])

                # If node is ZNode add measure_x circuit cycle
                elif type(node) == XNode:
                    qc.append(self._measure_x(i), range(num_nodes), [classicalBitLoc])

                # No else statement just in case node is a BaseNode and we strictly want to act on ZNode and XNode

            # Barrier for preventing overlap in gates
            qc.barrier()

        return qc

    def _measure_z(self, qZ):
        """
        Meausure Z quantum circuit cycle that is appended to the QuantumCircuit in the builder
        """
        assert type(qZ) is not list, "You must only give one Measure Z qubit"

        activeNeighbours = []
        for k in self.lattice.graph[qZ]:
            if k.active == True:
                activeNeighbours.append(k.node)

        qc = ConstrainedQuantumCircuit(self.lattice, self.num_nodes, 1)

        qc.id([qZ])
        qc.reset([qZ])
        for i in activeNeighbours:
            qc.cx(i, qZ)

        qc.measure([qZ], [0])
        qc.id([qZ])

        return qc.to_instruction(label="measure_z")

    def _measure_x(self, qX):
        """
        Meausure X quantum circuit cycle that is appended to the QuantumCircuit in the builder
        """
        assert type(qX) is not list, "You must only give one Measure X qubit"

        activeNeighbours = []
        for k in self.lattice.graph[qX]:
            if k.active == True:
                activeNeighbours.append(k.node)
        qc = ConstrainedQuantumCircuit(self.lattice, self.num_nodes, 1)

        qc.reset([qX])
        qc.h([qX])
        for i in activeNeighbours:
            qc.cx(qX, i)

        qc.h([qX])
        qc.measure([qX], [0])

        return qc.to_instruction(label="measure_x")
    

class HeavyHexCode(BaseCycle):
    def __init__(self, lattice):
        assert isinstance(lattice, HeavyHexLattice)

        super().__init__(lattice)

    def _circuit(self, num_cycles=1):
        """
        Returns the heavy hex code QuantumCircuit depending on the number of cycles specified
        :param num_cycles: Number of full cycles the heavy hex code will be runned.
        """
        num_nodes = self.num_nodes
        qc = ConstrainedQuantumCircuit(self.lattice, num_nodes)


        for j in range(num_cycles):
            # For every cycle add a classical register so we can track the changes in the heavy hex code
            qc.add_register(ClassicalRegister(num_nodes))

            # Iterate through names of nodes in heavy hex lattice
            # TODO Change lattice.node structure to contain tuples or be a dictionary
            for i in self.lattice.graph.keys():
                node = self.lattice.nodes[i]
                classicalBitLoc = i + j * num_nodes
                # # If node is FlagNode add measure_z circuit cycle
                if type(node) == FlagNode:
                    # print(i)
                    qc.append(self._measure_z(i), range(num_nodes), [classicalBitLoc])

                # If node is AncillaNode add measure_x circuit cycle
                if type(node) == AncillaNode:
                    neighbour1 = self.lattice.graph[i][0].node
                    neighbour2 = self.lattice.graph[i][1].node

                    if type(self.lattice.nodes[neighbour1]) is DataNode:
                        assert type(self.lattice.nodes[neighbour2]) is DataNode
                        qc.append(self._measure_x_2(i), range(num_nodes), [classicalBitLoc])

                    if type(self.lattice.nodes[neighbour1]) is FlagNode:
                        classicalBit1 =  neighbour1 + j * num_nodes
                        classicalBit2 =  neighbour2 + j * num_nodes
                        qc.append(self._measure_x_4(i), range(num_nodes), [classicalBit1, classicalBit2, classicalBitLoc])

                #     print(neighbour1, neighbour2, i)


                # No else statement just in case node is a BaseNode and we strictly want to act on ZNode and XNode

            # Barrier for preventing overlap in gates
            qc.barrier()

        return qc
    
    def _measure_x_2(self, qX):
        assert type(qX) is not list,  "You must only give one Measure X qubit"
        assert type(self.lattice.nodes[qX]) is AncillaNode, "The given qubit must be an Ancilla qubit"
        
        dataNeighbours = []
        for k in self.lattice.graph[qX]:
            if k.active == True:
                dataNeighbours.append(k.node)
                        
        qc = ConstrainedQuantumCircuit(self.lattice, self.num_nodes, 1)
        #Initialize in Z basis
        qc.reset(qX)
        qc.cx(qX, dataNeighbours[1])
        qc.cx(qX, dataNeighbours[0])
        qc.measure([qX], 0)

        return qc.to_instruction(label="measure_x_2")
        # return qc

    def _measure_x_4(self, qX):
        """
        Our ancilla is connected like this:
        D0         D2 
        |          |
        F0 -- A -- F1    or this    D0 -- A -- D1
        |          |
        D1         D3 
        """
        assert type(qX) is not list,  "You must only give one Measure X qubit"
        assert type(self.lattice.nodes[qX]) is AncillaNode, "The given qubit must be an Ancilla qubit"
        
        dataNeighbours = []
        flagNeighbours = []
        for k in self.lattice.graph[qX]:
            if k.active == True:
                flagNeighbours.append(k.node)

        for flag in flagNeighbours:
            for k in self.lattice.graph[flag]:
                # Add neighbours that is not the measure x qubit
                if k.active == True and k.node != qX:
                    dataNeighbours.append(k.node)
                    assert type(self.lattice.nodes[k.node]) is DataNode

        qc = ConstrainedQuantumCircuit(self.lattice, self.num_nodes, 3)
        #Initialize in X basis
        qc.reset([qX])
        qc.h([qX])
        #Initialize in Z basis
        qc.reset(flagNeighbours)
        qc.cx(qX, flagNeighbours[1])
        qc.cx(qX, flagNeighbours[0])
        # I think order matters check Fig 4 of the heavy hex code paper by ibm
        qc.cx(flagNeighbours[1], dataNeighbours[2])
        qc.cx(flagNeighbours[0], dataNeighbours[1])
        qc.cx(flagNeighbours[1], dataNeighbours[3])
        qc.cx(flagNeighbours[0], dataNeighbours[0])
        qc.cx(qX, flagNeighbours[1])
        qc.cx(qX, flagNeighbours[0])

        qc.measure(flagNeighbours, [0, 1])
        # Measure in X basis
        qc.h([qX])
        qc.measure([qX], [2])

        return qc.to_instruction(label="measure_x_4")          
        # return qc


    def _measure_z(self, qZ):
        """
        Our flag qZ is connected like this:
        D0
        |
        F0
        |
        D1
        """
        assert type(qZ) is not list,  "You must only give one Measure Z qubit"
        assert type(self.lattice.nodes[qZ]) is FlagNode, "The given qubit must be an Flag qubit"
        
        dataNeighbours = []
        for k in self.lattice.graph[qZ]:
            if k.active == True and type(self.lattice.nodes[k.node]) is not AncillaNode:
                dataNeighbours.append(k.node)
                assert type(self.lattice.nodes[k.node]) is DataNode

        
        qc = ConstrainedQuantumCircuit(self.lattice, self.num_nodes, 1)
        #Initialize in Z basis
        qc.reset(qZ)
        qc.cx(dataNeighbours[1], qZ)
        qc.cx(dataNeighbours[0], qZ)
        qc.measure([qZ], 0)

        # return qc
        return qc.to_instruction(label="measure_z")